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
from tomato.lib import tasks, db

class Connector(attributes.Mixin, models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('external', 'External Network') )
	name = models.CharField(max_length=20)
	from tomato.topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)

	attrs = db.JSONField(default={})

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

	def start(self, direct):
		fault.check(self.state == State.PREPARED, "Connector must be prepared to be started but is %s: %s", (self.state, self.name))
		proc = tasks.Process("start")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTaskSet("start", self.upcast().getStartTasks())
		return self.topology.startProcess(proc, direct)
		
	def stop(self, direct):
		fault.check(self.state != State.CREATED, "Connector must be started or prepared to be stopped but is %s: %s", (self.state, self.name))
		proc = tasks.Process("stop")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTaskSet("stop", self.upcast().getStopTasks())
		return self.topology.startProcess(proc, direct)

	def prepare(self, direct):
		fault.check(self.state == State.CREATED, "Connector must be created to be prepared but is %s: %s", (self.state, self.name))
		for con in self.connectionSetAll():
			dev = con.interface.device
			fault.check(dev.state != State.CREATED, "Device %s must be prepared before connector %s", (dev.name, self.name))
		proc = tasks.Process("prepare")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTaskSet("prepare", self.upcast().getPrepareTasks())
		return self.topology.startProcess(proc, direct)

	def destroy(self, direct):
		fault.check(self.state != State.STARTED, "Connector must not be started to be destroyed but is %s: %s", (self.state, self.name))
		proc = tasks.Process("destroy")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTaskSet("destroy", self.upcast().getDestroyTasks())
		return self.topology.startProcess(proc, direct)

	def _changeState(self, state):
		self.state = state
		self.save()

	def getStartTasks(self):
		taskset = tasks.TaskSet()
		taskset.addLastTask(tasks.Task("change-state", self._changeState, args=(State.STARTED,)))
		return taskset
	
	def getStopTasks(self):
		taskset = tasks.TaskSet()
		taskset.addLastTask(tasks.Task("change-state", self._changeState, args=(State.PREPARED,)))
		return taskset
	
	def getPrepareTasks(self):
		taskset = tasks.TaskSet()
		taskset.addLastTask(tasks.Task("change-state", self._changeState, args=(State.PREPARED,)))
		return taskset
	
	def getDestroyTasks(self):
		taskset = tasks.TaskSet()
		taskset.addLastTask(tasks.Task("change-state", self._changeState, args=(State.CREATED,)))
		return taskset
	
	def __unicode__(self):
		return self.name
				
	def updateResourceUsage(self):
		res = self.upcast().getResourceUsage()
		self.setAttribute("resources",res)
	
	def bridgeName(self, interface):
		return "gbr_%s" % interface.connection.bridgeId()

	def configure(self, properties):
		if "pos" in properties:
			self.setAttribute("pos", properties["pos"])
		self.save()

	def toDict(self, auth):
		"""
		Prepares a connector for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the connector
		@rtype: dict
		"""
		res = {"attrs": {"name": self.name, "type": self.type, "state": self.state,
					"pos": self.getAttribute("pos"),
				},
			"resources": self.getAttribute("resources"),
			"connections": dict([[str(c.interface), c.upcast().toDict(auth)] for c in self.connectionSetAll()]),
			}
		return res


class Connection(attributes.Mixin, models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(devices.Interface)
	bridge_id = models.PositiveIntegerField(null=True)

	attrs = db.JSONField(default={})

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

	def bridgeId(self):
		if not self.bridge_id:
			self.bridge_id = self.interface.device.host.nextFreeBridge()
			self.save()
		return self.bridge_id

	def bridgeName(self):
		return self.connector.upcast().bridgeName(self.interface)

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
		pass

	def toDict(self, auth):
		"""
		Prepares a connection for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the connection
		@rtype: dict
		"""
		res = {"interface": str(self.interface), "attrs":{"bridge_id": self.bridge_id}}
		return res
