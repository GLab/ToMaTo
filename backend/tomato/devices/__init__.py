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

import fault, hosts, attributes
from lib import tasks

class Device(models.Model):
	TYPE_OPENVZ="openvz"
	TYPE_KVM="kvm"
	TYPES = ( (TYPE_OPENVZ, 'OpenVZ'), (TYPE_KVM, 'KVM') )
	name = models.CharField(max_length=20)
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	host = models.ForeignKey(hosts.Host, null=True)
	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)

	def init(self):
		pass
		
	def interfaceSetGet(self, name):
		return self.interface_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def interfaceSetAdd(self, iface):
		return self.interface_set.add(iface) # pylint: disable-msg=E1101

	def interfaceSetAll(self):
		return self.interface_set.all() # pylint: disable-msg=E1101

	def upcast(self):
		if self.isKvm():
			return self.kvmdevice.upcast() # pylint: disable-msg=E1101
		if self.isOpenvz():
			return self.openvzdevice.upcast() # pylint: disable-msg=E1101
		return self

	def isOpenvz(self):
		return self.type == Device.TYPE_OPENVZ

	def isKvm(self):
		return self.type == Device.TYPE_KVM
	
	def hostPreferences(self):
		prefs = ObjectPreferences(True)
		for h in hosts.getAll(self.attributes.get("hostgroup")):
			if h.enabled:
				prefs.add(h, 1.0 - len(h.device_set.all())/100.0)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def hostOptions(self):
		options = self.hostPreferences()
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				options = options.combine(iface.connection.connector.upcast().hostPreferences())
		return options

	def downloadSupported(self):
		return False
		
	def uploadSupported(self):
		return False
		
	def bridgeName(self, interface):
		"""
		Returns the name of the bridge for the connection of the given interface
		Note: This must be 16 characters or less for brctl to work
		@param interface the interface
		"""
		try:
			return interface.connection.bridgeName()
		except: #pylint: disable-msg=W0702
			return None		
	
	def migrate(self, direct):
		proc = tasks.Process("migrate")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTask(tasks.Task("migrate", self.upcast().migrateRun))
		return self.topology.startProcess(proc, direct)

	def start(self, direct):
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		proc = tasks.Process("start")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTaskSet("start", self.upcast().getStartTasks())
		return self.topology.startProcess(proc, direct)
		
	def stop(self, direct):
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		proc = tasks.Process("stop")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTaskSet("stop", self.upcast().getStopTasks())
		return self.topology.startProcess(proc, direct)

	def prepare(self, direct):
		if self.state == State.PREPARED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		proc = tasks.Process("prepare")
		proc.addTask(tasks.Task("renew", self.topology.renew))
		proc.addTaskSet("prepare", self.upcast().getPrepareTasks())
		return self.topology.startProcess(proc, direct)

	def destroy(self, direct):
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector
				if not con.isExternal() and not con.state == State.CREATED:
					raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Connector must be destroyed first: %s" % con )		
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
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
	
	def configure(self, properties):
		if "hostgroup" in properties:
			assert self.state == State.CREATED, "Cannot change hostgroup of prepared device: %s" % self.name
			if properties["hostgroup"] == "auto":
				properties["hostgroup"] = ""
		for key in properties:
			self.attributes[key] = properties[key]
		del self.attributes["host"]			
		del self.attributes["name"]			
		del self.attributes["type"]			
		del self.attributes["state"]			
		del self.attributes["download_supported"]			
		del self.attributes["upload_supported"]			
		self.save()

	def updateResourceUsage(self):
		res = self.upcast().getResourceUsage()
		for key in res:
			self.attributes["resources_%s" % key] = res[key]

	def __unicode__(self):
		return self.name
		
	def toDict(self, auth):
		"""
		Prepares a device for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the device
		@rtype: dict
		"""
		res = {"attrs": {"host": str(self.host) if self.host else None,
					"name": self.name, "type": self.type, "state": self.state,
					"download_supported": self.downloadSupported(), "upload_supported": self.uploadSupported() 
					},
			"interfaces": dict([[i.name, i.upcast().toDict(auth)] for i in self.interfaceSetAll()]),
		}
		res["attrs"].update(self.attributes.items())
		return res
	
	def uploadImageGrant(self, redirect):
		import uuid
		if self.host:
			filename = str(uuid.uuid1())
			redirect = redirect % filename
			return {"upload_url": self.host.upload_grant(filename, redirect), "redirect_url": redirect}
		else:
			return None
				
	def useUploadedImage(self, filename):
		path = "%s/%s" % (self.host.attributes["hostserver_basedir"], filename)
		proc = tasks.Process("use-uploaded-image")
		proc.addTask("main", self.upcast().useUploadedImageRun, args=(path,))
		return proc.start()
			
			
class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)
	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)

	def init(self):
		pass
		
	def isConfigured(self):
		try:
			self.configuredinterface # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False
	
	def isConnected(self):
		try:
			self.connection # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False	
	
	def configure(self, properties):
		for key in properties:
			self.attributes[key] = properties[key]
		del self.attributes["name"]			
		self.save()

	def upcast(self):
		if self.isConfigured():
			return self.configuredinterface.upcast() # pylint: disable-msg=E1101
		return self

	def __unicode__(self):
		return str(self.device.name)+"."+str(self.name)
		
	def toDict(self, auth):
		"""
		Prepares an interface for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the interface
		@rtype: dict
		"""
		res = {"attrs": {"name": self.name}}
		res["attrs"].update(self.attributes.items())
		return res

	def getStartTasks(self):
		return tasks.TaskSet()
	
	def getStopTasks(self):
		return tasks.TaskSet()
	
	def getPrepareTasks(self):
		return tasks.TaskSet()
	
	def getDestroyTasks(self):
		return tasks.TaskSet()
