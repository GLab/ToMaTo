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

from tomato import attributes, hosts
from tomato.topology import Topology
from tomato.generic import State, ObjectPreferences
from tomato.lib import db, hostserver

class Device(db.ReloadMixin, attributes.Mixin, models.Model):
	TYPE_OPENVZ="openvz"
	TYPE_KVM="kvm"
	TYPES = ( (TYPE_OPENVZ, 'OpenVZ'), (TYPE_KVM, 'KVM') )
	name = models.CharField(max_length=20, validators=[db.nameValidator])
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, validators=[db.nameValidator], choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	host = models.ForeignKey(hosts.Host, null=True)
	hostgroup = models.CharField(max_length=20, validators=[db.nameValidator], null=True)

	attrs = db.JSONField()
	
	class Meta:
		unique_together = (("topology", "name"),)

	def init(self):
		self.attrs = {}
		
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
		for h in hosts.getAll(self.hostgroup):
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
		return interface.connection.bridgeName()
	
	def migrate(self, direct):
		proc = tasks.Process("migrate")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add(tasks.Task("migrate", self.upcast().migrateRun))
		return self.topology.startProcess(proc, direct)

	def start(self, direct):
		fault.check(self.state == State.PREPARED, "Device must be prepared to be started but is %s: %s", (self.state, self.name))
		proc = tasks.Process("start")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add("start", self.upcast().getStartTasks())
		return self.topology.startProcess(proc, direct)
		
	def stop(self, direct):
		fault.check(self.state != State.CREATED, "Device must be started or prepared to be stopped but is %s: %s", (self.state, self.name))
		proc = tasks.Process("stop")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add("stop", self.upcast().getStopTasks())
		return self.topology.startProcess(proc, direct)

	def prepare(self, direct):
		fault.check(self.state == State.CREATED, "Device must be created to be prepared but is %s: %s", (self.state, self.name))
		proc = tasks.Process("prepare")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add("prepare", self.upcast().getPrepareTasks())
		return self.topology.startProcess(proc, direct)

	def destroy(self, direct):
		fault.check(self.state != State.STARTED, "Device must not be started to be destroyed but is %s: %s", (self.state, self.name))
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector
				fault.check(con.state == State.CREATED, "Connector %s must be destroyed before device %s", (con.name, self.name))
		proc = tasks.Process("destroy")
		proc.add(tasks.Task("renew", self.topology.renew))
		proc.add("destroy", self.upcast().getDestroyTasks())
		return self.topology.startProcess(proc, direct)

	def _changeState(self, state):
		self.state = state
		self.save()

	def getStartTasks(self):
		taskset = tasks.TaskSet()
		taskset.add(tasks.Task("change-state", self._changeState, args=(State.STARTED,), after=taskset))
		return taskset
	
	def getStopTasks(self):
		taskset = tasks.TaskSet()
		taskset.add(tasks.Task("change-state", self._changeState, args=(State.PREPARED,), after=taskset))
		return taskset
	
	def getPrepareTasks(self):
		taskset = tasks.TaskSet()
		taskset.add(tasks.Task("change-state", self._changeState, args=(State.PREPARED,), after=taskset))
		return taskset
	
	def getDestroyTasks(self):
		taskset = tasks.TaskSet()
		taskset.add(tasks.Task("change-state", self._changeState, args=(State.CREATED,), after=taskset))
		return taskset
	
	def configure(self, properties):
		if "hostgroup" in properties:
			fault.check(self.state == State.CREATED, "Cannot change hostgroup of prepared device: %s" % self.name)
			if properties["hostgroup"] == "auto":
				properties["hostgroup"] = ""
		if "pos" in properties:
			self.setAttribute("pos", properties["pos"])
		self.save()

	def updateResourceUsage(self):
		res = self.upcast().getResourceUsage()
		self.setAttribute("resources",res)

	def __unicode__(self):
		return self.name
		
	def getIdUsage(self):
		ids = {}
		for iface in self.interfaceSetAll():
			for (key, value) in iface.upcast().getIdUsage().iteritems():
				ids[key] = ids.get(key, set()) | value
		return ids
		
	def toDict(self, auth):
		"""
		Prepares a device for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the device
		@rtype: dict
		"""
		res = {"attrs": {"host": str(self.host) if self.host else None,
					"pos": self.getAttribute("pos"),
					"name": self.name, "type": self.type, "state": self.state,
					"download_supported": self.downloadSupported(), "upload_supported": self.uploadSupported() 
					},
			"resources" : self.getAttribute("resources"),
			"interfaces": dict([[i.name, i.upcast().toDict(auth)] for i in self.interfaceSetAll()]),
		}
		return res
	
	def uploadImageGrant(self, redirect):
		import uuid
		if self.host:
			filename = str(uuid.uuid1())
			redirect = redirect % {"filename": filename}
			return {"upload_url": hostserver.uploadGrant(self.host, filename, redirect), "redirect_url": redirect, "filename": filename}
		else:
			return None
				
	def useUploadedImage(self, filename, direct=False):
		path = "%s/%s" % (self.host.hostServerBasedir(), filename)
		proc = tasks.Process("use-uploaded-image")
		proc.add(tasks.Task("main", self.upcast().useUploadedImageRun, args=(path,)))
		return proc.start(direct)
			
			
class Interface(attributes.Mixin, models.Model):
	name = models.CharField(max_length=5, validators=[db.ifaceValidator])
	device = models.ForeignKey(Device)

	attrs = db.JSONField(default={})

	class Meta:
		unique_together = (("device", "name"),)

	def init(self):
		self.attrs = {}
		
	def getIdUsage(self):
		return {}
		
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
		pass

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
		return res

	def getStartTasks(self):
		return tasks.TaskSet()
	
	def getStopTasks(self):
		return tasks.TaskSet()
	
	def getPrepareTasks(self):
		return tasks.TaskSet()
	
	def getDestroyTasks(self):
		return tasks.TaskSet()

# keep internal imports at the bottom to avoid dependency problems
from tomato import fault
from tomato.lib import tasks
