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

from tomato import config, fault
from tomato.hosts import templates, resources
from tomato.generic import State
from tomato.devices import Device, Interface, common
from tomato.topology import Permission

from django.db import models
import hashlib

from tomato.lib import util, repy, ifaceutil, hostserver, tasks, db, exceptions

class ProgDevice(common.RepairMixin, common.TemplateMixin, common.VMIDMixin, common.VNCMixin, Device):

	vnc_port = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	template = models.CharField(max_length=255, null=True, validators=[db.templateValidator])

	class Meta:
		db_table = "tomato_progdevice"
		app_label = 'tomato'

	def upcast(self):
		return self

	def init(self):
		self.attrs = {}

	def setArgs(self, value):
		self.setAttribute("args", value)

	def getArgs(self):
		return self.getAttribute("args", [])

	def getState(self):
		if not self.host:
			return State.CREATED
		return repy.getState(self.host, self.id) 

	def getCapabilities(self, user):
		capabilities = Device.getCapabilities(self, user)
		isUser = self.topology.checkAccess(Permission.ROLE_USER, user)
		capabilities["configure"].update({
			"template": self.state == State.CREATED,
			"args": self.state != State.STARTED,
		})
		capabilities.update(other={
			"console": isUser and self.getVncPort() and self.state == State.STARTED
		})
		return capabilities
	
	def getVmid(self):
		#for vncPassword
		return self.id

	def _startVnc(self):
		if self._vncRunning():
			return
		repy.startVnc(self.host, self.id, self.getVncPort(), self.vncPassword())

	def _vncRunning(self):
		return self.getVncPort() and repy.vncRunning(self.host, self.id, self.getVncPort())

	def connectToBridge(self, iface, bridge):
		ifaceutil.bridgeCreate(self.host, bridge)
		ifaceutil.bridgeConnect(self.host, bridge, self.interfaceDevice(iface))
		ifaceutil.ifup(self.host, bridge)

	def _createBridges(self):
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				bridge = self.getBridge(iface)
				assert bridge, "Interface has no bridge %s" % iface
				ifaceutil.bridgeCreate(self.host, bridge)
				ifaceutil.ifup(self.host, bridge)

	def _startDev(self):
		host = self.host
		vmid = self.id
		state = repy.getState(host, vmid)
		if not self.getVncPort():
			self._assignVncPort()
		if state == State.CREATED:
			self._prepareDev()
			state = repy.getState(host, vmid)
		for iface in self.interfaceSetAll():
			bridge = self.getBridge(iface)
			assert bridge, "Interface has no bridge %s" % iface
			ifaceutil.bridgeCreate(self.host, bridge)
			ifaceutil.ifup(self.host, bridge)
		try: 
			if state == State.PREPARED:
				ifaces = [iface.name for iface in self.interfaceSetAll()]
				repy.start(host, vmid, ifaces, self.getArgs())
			for iface in self.interfaceSetAll():
				repy.waitForInterface(self.host, self.id, iface.name)
				ifaceutil.ifup(self.host, self.interfaceDevice(iface))
				self.connectToBridge(iface, self.getBridge(iface))
			self._startVnc()
			self.state = State.STARTED
			self.save()
		except:
			try:
				repy.stop(host, vmid)
			except:
				pass
			raise
	
	def getStartTasks(self):
		taskset = Device.getStartTasks(self)
		taskset.add(tasks.Task("start", self._startDev))
		return taskset
	
	def _stopDev(self):
		host = self.host
		vmid = self.id
		state = repy.getState(host, vmid)
		if state == State.STARTED:
			repy.stop(host, vmid)
			state = repy.getState(host, vmid)
		self.state = State.PREPARED
		self.save()
		if self.getVncPort():
			repy.stopVnc(host, vmid, self.getVncPort())
			self._unassignVncPort()

	def getStopTasks(self):
		taskset = Device.getStopTasks(self)
		taskset.add(tasks.Task("stop", self._stopDev))
		return taskset

	def _unassignHost(self):
		self.host = None
		self.save()

	def _assignHost(self):
		if not self.host:
			self.host = self.hostOptions().best()
			fault.check(self.host, "No matching host found")
			self.save()

	def selectHost(self):
		self._assignHost()

	def _prepareDev(self):
		#assign host
		self._assignHost()
		host = self.host
		
		self._assignBridges()
		
		vmid = self.id
		
		state = repy.getState(host, vmid)
		if state == State.STARTED:
			repy.stop(host, vmid)
			state = repy.getState(host, vmid)
		if state == State.PREPARED:
			self.state = repy.getState(host, vmid)
			self.save()
			return
		assert state == State.CREATED
		
		#nothing happened until here
		
		repy.create(host, vmid, self.getTemplate())
		try:
			self.state = State.PREPARED
			self.save()
		except:
			try:
				repy.destroy(host, vmid)
			except:
				pass
			raise

	def getPrepareTasks(self):
		taskset = Device.getPrepareTasks(self)
		taskset.add(tasks.Task("prepare", self._prepareDev))
		return taskset

	def _destroyDev(self):
		host = self.host
		vmid = self.id
		if not host:
			return
		if vmid:
			state = repy.getState(host, vmid)
			if state == State.STARTED:
				repy.stop(host, vmid)
				state = repy.getState(host, vmid)
			if state == State.PREPARED:
				repy.destroy(host, vmid)
				state = repy.getState(host, vmid)
			assert state == State.CREATED
			self.state = State.CREATED
			self.save()
		self._unassignBridges()
		self._unassignHost()

	def getDestroyTasks(self):
		taskset = Device.getDestroyTasks(self)
		taskset.add(tasks.Task("destroy", self._destroyDev))
		return taskset

	def configure(self, properties):
		if "template" in properties:
			fault.check(self.state == State.CREATED, "Cannot change template of prepared device: %s" % self.name)
		if "args" in properties:
			fault.check(self.state != State.STARTED, "Cannot change arguments of running device: %s" % self.name)
		Device.configure(self, properties)
		if "template" in properties:
			self.setTemplate(properties["template"])
		if "args" in properties:
			self.setArgs(properties["args"])
		self.save()

	def interfacesAdd(self, name, properties):
		fault.check(self.state != State.STARTED, "Repy does not support adding interfaces to running VMs: %s" % self.name)
		import re
		fault.check(re.match("eth(\d+)", name), "Invalid interface name: %s" % name)
		try:
			fault.check(not self.interfaceSetGet(name), "Duplicate interface name: %s" % name)
		except Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface = Interface()
		iface.name = name
		iface.device = self
		iface.init()
		iface.save()
		Device.interfaceSetAdd(self, iface)

	def interfacesConfigure(self, name, properties):
		pass

	def interfacesRename(self, name, properties):
		iface = self.interfaceSetGet(name).upcast()
		try:
			fault.check(not self.interfaceSetGet(properties["name"]), "Duplicate interface name: %s" % properties["name"])
		except Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface.name = properties["name"]
		iface.save()

	def interfacesDelete(self, name):
		iface = self.interfaceSetGet(name).upcast()
		if iface.isConnected():
			iface.connection.connector.upcast().connectionsDelete(unicode(iface))
		iface.delete()

	def useUploadedImageRun(self, path):
		assert self.state == State.PREPARED, "Upload not supported"
		repy.useImage(self.host, self.id, path)

	def checkUploadedImage(self, path):
		error = repy.check(self.host, path)
		if error:
			raise fault.new("Invalid/Unsafe code: %s, %s" % error, fault.USER_ERROR)

	def downloadImageUri(self):
		assert self.state == State.PREPARED, "Download not supported"
		filename = "%s_%s.repy" % (self.topology.name, self.name)
		file = self.host.getHostServer().randomFilename()
		repy.copyImage(self.host, self.id, file)
		return self.host.getHostServer().downloadGrant(file, filename)

	def getResourceUsage(self):
		disk = 0
		memory = 0
		ports = 1 if self.state == State.STARTED else 0		
		if self.host:
			disk = repy.getDiskUsage(self.host, self.id)
			memory = repy.getMemoryUsage(self.host, self.id)
		traffic = 0
		if self.state == State.STARTED:
			for iface in self.interfaceSetAll():
				dev = self.interfaceDevice(iface)
				traffic += ifaceutil.getRxBytes(self.host, dev)
				traffic += ifaceutil.getTxBytes(self.host, dev)
		return {"disk": disk, "memory": memory, "ports": ports, "traffic": traffic}		

	def interfaceDevice(self, iface):
		return repy.interfaceDevice(self.id, iface.name)

	def toDict(self, auth):
		res = Device.toDict(self, auth)
		res["attrs"].update(vnc_port=self.getVncPort(), template=self.getConfiguredTemplate(), args=self.getArgs())
		if auth:
			res["attrs"].update(vnc_password = self.vncPassword())
		return res				