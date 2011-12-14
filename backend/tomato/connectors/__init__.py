# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.db import models

from tomato import fault, hosts, attributes, devices
from tomato.generic import State, ObjectPreferences
from tomato.lib import tasks, db, ifaceutil, util
from tomato.topology import Topology, Permission
from tomato.lib.decorators import *

class Connector(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
	name = models.CharField(max_length=20, validators=[db.nameValidator])
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, validators=[db.nameValidator], choices=( ('vpn', 'VPN'), ('external', 'External Network') ))
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)

	attrs = db.JSONField(default={})

	class Meta:
		unique_together = (("topology", "name"),)
		ordering=["name"]

	def init(self):
		self.attrs = {}
		self.save()
		
	def connectionSetAdd(self, con):
		return self.connection_set.add(con) # pylint: disable-msg=E1101

	def connectionSetAll(self):
		return self.connection_set.all() # pylint: disable-msg=E1101

	def connectionSetGet(self, interface):
		return self.connection_set.get(interface=interface).upcast() # pylint: disable-msg=E1101

	def isVPN(self):
		return self.type=='vpn'

	def isExternal(self):
		return self.type=='external'

	def upcast(self):
		if self.isVPN():
			return self.tincconnector.upcast() # pylint: disable-msg=E1101
		if self.isExternal():
			return self.externalnetworkconnector.upcast() # pylint: disable-msg=E1101
		return self

	def hostPreferences(self):
		prefs = ObjectPreferences()
		# keep it local
		sites={}
		for c in self.connectionSetAll():
			dev = c.interface.device
			if dev.host:
				#discourage devices on the same host
				prefs.add(dev.host, -0.05)
				sites[dev.host.group] = sites.get(dev.host.group, 0.0) + 1.0
		for site, num in sites.iteritems():
			val = 0.05 * num/(num+10)
			# value increases with hosts already at that site
			# value is bounded by 0.01
			for h in hosts.getAll(site):
				prefs.add(h, val)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def affectedHosts(self):
		return hosts.Host.objects.filter(device__interface__connection__connector=self).distinct() # pylint: disable-msg=E1101

	def getCapabilities(self, user):
		isUser = self.topology.checkAccess(Permission.ROLE_USER, user)
		isBusy = self.topology.isBusy()
		minDevState = State.STARTED
		maxDevState = State.CREATED
		for con in self.connectionSetAll():
			dev = con.interface.device
			if dev.state == State.STARTED:
				maxDevState = State.STARTED
			elif dev.state == State.CREATED:
				minDevState = State.CREATED
			else: #prepared
				if minDevState == State.STARTED:
					minDevState = State.PREPARED
				if maxDevState == State.CREATED:
					maxDevState = State.PREPARED
		return {
			"action": {
				"start": isUser and not isBusy and self.state == State.PREPARED, 
				"stop": isUser and not isBusy and self.state == State.STARTED,
				"prepare": isUser and not isBusy and self.state == State.CREATED and minDevState != State.CREATED,
				"destroy": isUser and not isBusy and self.state == State.PREPARED,
			},
			"configure": {
			},
			"modify": {
				"delete": self.state == State.CREATED,
				"connections": self.state != State.STARTED
			}
		}
		
	def action(self, user, action, attrs, direct):
		capabilities = self.getCapabilities(user)
		fault.check(action in capabilities["action"], "Unknown action: %s", action)
		fault.check(capabilities["action"][action], "Action %s not available", action)
		return self._runAction(action, attrs, direct)
	
	def _runAction(self, action, attrs, direct):
		if action == "start":
			return self.start(direct)
		elif action == "stop":
			return self.stop(direct)
		elif action == "prepare":
			return self.prepare(direct)
		elif action == "destroy":
			return self.destroy(direct)

	def start(self, direct, noProcess=False):
		fault.check(self.state == State.PREPARED, "Connector must be prepared to be started but is %s: %s", (self.state, self.name))
		proc = tasks.Process("start")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add(self.upcast().getStartTasks())
		if noProcess:
			return proc.start(direct)
		return self.topology.startProcess(proc, direct)
		
	def stop(self, direct, noProcess=False):
		fault.check(self.state != State.CREATED, "Connector must be started or prepared to be stopped but is %s: %s", (self.state, self.name))
		proc = tasks.Process("stop")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add(self.upcast().getStopTasks())
		if noProcess:
			return proc.start(direct)
		return self.topology.startProcess(proc, direct)

	def prepare(self, direct, noProcess=False):
		fault.check(self.state == State.CREATED, "Connector must be created to be prepared but is %s: %s", (self.state, self.name))
		for con in self.connectionSetAll():
			dev = con.interface.device
			fault.check(dev.state != State.CREATED, "Device %s must be prepared before connector %s", (dev.name, self.name))
		proc = tasks.Process("prepare")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add(self.upcast().getPrepareTasks())
		if noProcess:
			return proc.start(direct)
		return self.topology.startProcess(proc, direct)

	def destroy(self, direct, noProcess=False):
		fault.check(self.state != State.STARTED, "Connector must not be started to be destroyed but is %s: %s", (self.state, self.name))
		proc = tasks.Process("destroy")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add(self.upcast().getDestroyTasks())
		if noProcess:
			return proc.start(direct)
		return self.topology.startProcess(proc, direct)

	def _changeState(self, state):
		self.state = state
		self.save()

	def _adaptTaskset(self, taskset):
		taskset.before(taskset.find("change-state"))
		return taskset

	def _initialTasks(self, state):
		taskset = tasks.TaskSet()
		taskset.add(tasks.Task("change-state", self._changeState, args=(state,)))
		return taskset

	def getStartTasks(self):
		return self._initialTasks(State.STARTED)
	
	def getStopTasks(self):
		return self._initialTasks(State.PREPARED)
	
	def getPrepareTasks(self):
		return self._initialTasks(State.PREPARED)
	
	def getDestroyTasks(self):
		return self._initialTasks(State.CREATED)
	
	def __unicode__(self):
		return self.name
				
	def updateResourceUsage(self):
		res = self.upcast().getResourceUsage()
		self.setAttribute("resources",res)
	
	def configure(self, properties):
		self.setPrivateAttributes(properties)

	def onInterfaceStateChange(self, connection):
		pass

	def repair(self):
		pass

	@xmlRpcSafe
	def toDict(self, user):
		res = {"attrs": {"name": self.name, "type": self.type, "state": self.state},
			"resources": util.xml_rpc_sanitize(self.getAttribute("resources")),
			"connections": dict([[str(c.interface), c.upcast().toDict(user)] for c in self.connectionSetAll()]),
			"capabilities": self.getCapabilities(user)
			}
		res["attrs"].update(self.getPrivateAttributes())
		return res


class Connection(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(devices.Interface)

	attrs = db.JSONField(default={})

	class Meta:
		unique_together = (("connector", "interface"),)
		
	def getHost(self):
		if not self.interface:
			return None
		if not self.interface.device.host:
			self.interface.device.reload()
		return self.interface.device.host

	def init(self):
		self.attrs = {}
		self.save()
		
	def isEmulated(self):
		try:
			self.emulatedconnection # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False

	def upcast(self):
		if self.isEmulated():
			return self.emulatedconnection.upcast() # pylint: disable-msg=E1101
		return self

	def getBridge(self, create=True):
		return self.connector.upcast().getBridge(self, create=create)

	def prepareBridge(self):
		pass

	def destroyBridge(self):
		pass

	def getStartTasks(self):
		return tasks.TaskSet()
	
	def getStopTasks(self):
		return tasks.TaskSet()
	
	def getPrepareTasks(self):
		return tasks.TaskSet()
	
	def getDestroyTasks(self):
		return tasks.TaskSet()
				
	def __unicode__(self):
		return unicode(self.connector) + "<->" + unicode(self.interface)

	def configure(self, properties):
		self.setPrivateAttributes(properties)

	def getCapabilities(self, user):
		return {
			"action": {},
			"configure": {},
		}

	def toDict(self, user):
		res = {"interface": str(self.interface), "attrs":{}}
		if user:
			res["capabilities"] = self.getCapabilities(user)
		res["attrs"].update(self.getPrivateAttributes())
		return res
