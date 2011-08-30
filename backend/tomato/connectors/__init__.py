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

class Connector(db.ReloadMixin, attributes.Mixin, models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('external', 'External Network') )
	name = models.CharField(max_length=20, validators=[db.nameValidator])
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, validators=[db.nameValidator], choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)

	attrs = db.JSONField(default={})

	class Meta:
		unique_together = (("topology", "name"),)

	def init(self):
		self.attrs = {}
		
	def connectionSetAdd(self, con):
		return self.connection_set.add(con) # pylint: disable-msg=E1101

	def connectionSetAll(self):
		return self.connection_set.all() # pylint: disable-msg=E1101

	def connectionSetGet(self, interface):
		return self.connection_set.get(interface=interface).upcast() # pylint: disable-msg=E1101

	def isTinc(self):
		return self.type=='router' or self.type=='switch' or self.type=='hub'

	def isExternal(self):
		return self.type=='external'

	def upcast(self):
		if self.isTinc():
			return self.tincconnector.upcast() # pylint: disable-msg=E1101
		if self.isExternal():
			return self.externalnetworkconnector.upcast() # pylint: disable-msg=E1101
		return self

	def hostPreferences(self):
		prefs = ObjectPreferences()
		# keep it local
		for c in self.connectionSetAll():
			dev = c.interface.device
			if dev.host:
				prefs.add(dev.host, -0.1)
				for h in hosts.getAll(dev.host.group):
					prefs.add(h, 0.01)
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
				"pos": True
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
		self._triggerInterfaces()

	def _triggerInterfaces(self):
		for con in self.connectionSetAll():
			con.interface.upcast().onConnectionStateChange() 

	def _adaptTaskset(self, taskset):
		taskset.after(taskset.find("reload"))
		taskset.before(taskset.find("change-state"))
		return taskset

	def _initialTasks(self, state):
		taskset = tasks.TaskSet()
		taskset.add(tasks.Task("reload", self.reload))
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
	
	def getBridge(self, connection, create=True):
		bridge_id = connection.getBridgeId()
		assert bridge_id
		name = "gbr_%d" % bridge_id
		if create:
			host = connection.getHost()
			ifaceutil.bridgeCreate(host, name)
		return name

	def configure(self, properties):
		self.setPrivateAttributes(properties)

	def getIdUsage(self, host):
		ids = {}
		for con in self.connectionSetAll():
			for (key, value) in con.upcast().getIdUsage(host).iteritems():
				ids[key] = ids.get(key, set()) | value
		return ids

	def onInterfaceStateChange(self, connection):
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


class Connection(db.ReloadMixin, attributes.Mixin, models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(devices.Interface)
	bridge_id = models.PositiveIntegerField(null=True)

	attrs = db.JSONField(default={})

	class Meta:
		unique_together = (("connector", "interface"),)

	def getHost(self):
		if not self.interface:
			return None
		if not self.interface.device.host:
			self.interface.device.reload()
		return self.interface.device.host

	def getBridgeId(self):
		return self.bridge_id

	def getIdUsage(self, host):
		ids = {}
		if self.bridge_id and self.interface.device.host == host:
			ids.update(bridge=set((self.bridge_id,)))
		return ids

	def _setBridgeId(self, id):
		self.bridge_id = id
		self.save()

	def init(self):
		self.attrs = {}
		
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

	def _assignBridgeId(self):
		if not self.bridge_id:
			host = self.getHost()
			assert host
			host.takeId("bridge", self._setBridgeId)		

	def _unassignBridgeId(self):
		if self.bridge_id:
			host = self.getHost()
			if host:
				if not self.connector.isExternal():
					bridge = self.getBridge(create=False)
					if ifaceutil.bridgeExists(host, bridge):
						attachedInterfaces = ifaceutil.bridgeInterfaces(host, bridge)
						assert not attachedInterfaces, "Bridge %s still has interfaces connected: %s" % (bridge, attachedInterfaces) 
						ifaceutil.bridgeRemove(host, bridge)			
				host.giveId("bridge", self.bridge_id)
			self.bridge_id = None
			self.save()

	def getBridge(self, create=True):
		return self.connector.upcast().getBridge(self, create=create)

	def getStartTasks(self):
		return tasks.TaskSet()
	
	def getStopTasks(self):
		return tasks.TaskSet()
	
	def getPrepareTasks(self):
		return tasks.TaskSet()
	
	def getDestroyTasks(self):
		return tasks.TaskSet()
				
	def __unicode__(self):
		return str(self.connector) + "<->" + str(self.interface)

	def configure(self, properties):
		self.setPrivateAttributes(properties)

	def getCapabilities(self, user):
		return {
			"action": {},
			"configure": {}
		}

	def toDict(self, user):
		res = {"interface": str(self.interface), "attrs":{"bridge_id": self.bridge_id}}
		if user:
			res["capabilities"] = self.getCapabilities(user)
		res["attrs"].update(self.getPrivateAttributes())
		return res
