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
from tomato.hosts import templates
from tomato.generic import State
from tomato.devices import Device, Interface
from tomato.topology import Permission

from django.db import models
import hashlib

from tomato.lib import util, repy, ifaceutil, hostserver, tasks, db, exceptions

class ProgDevice(Device):

	vnc_port = models.PositiveIntegerField(null=True)
	template = models.CharField(max_length=255, null=True, validators=[db.templateValidator])

	class Meta:
		db_table = "tomato_progdevice"
		app_label = 'tomato'

	def upcast(self):
		return self

	def init(self):
		self.attrs = {}

	def setVncPort(self, value):
		self.vnc_port = value
		self.save()

	def getVncPort(self):
		return self.vnc_port

	def setTemplate(self, value):
		self.template = value
		self.save()

	def getTemplate(self):
		return self.template

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

	def vncPassword(self):
		if not self.getVncPort():
			return None 
		m = hashlib.md5()
		m.update(config.PASSWORD_SALT)
		m.update(str(self.name))
		m.update(str(self.id))
		m.update(str(self.getVncPort()))
		m.update(str(self.topology.owner))
		return m.hexdigest()
	
	def _startVnc(self):
		repy.startVnc(self.host, self.id, self.getVncPort(), self.vncPassword())

	def _startVm(self):
		repy.start(self.host, self.id, [iface.name for iface in self.interfaceSetAll()], self.getArgs())
		for iface in self.interfaceSetAll():
			repy.waitForInterface(self.host, self.id, iface.name)

	def connectToBridge(self, iface, bridge):
		ifaceutil.bridgeCreate(self.host, bridge)
		ifaceutil.bridgeConnect(self.host, bridge, self.interfaceDevice(iface))
		ifaceutil.ifup(self.host, bridge)

	def _startIface(self, iface):
		ifaceutil.ifup(self.host, self.interfaceDevice(iface))
		bridge = self.getBridge(iface)
		self.connectToBridge(iface, bridge)

	def _createBridges(self):
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				bridge = self.getBridge(iface)
				assert bridge, "Interface has no bridge %s" % iface
				ifaceutil.bridgeCreate(self.host, bridge)
				ifaceutil.ifup(self.host, bridge)

	def _fallbackStop(self):
		self.state = self.getState()
		self.save()
		if self.state == State.STARTED:
			self._stopVm()
		if self.getVncPort():
			self._stopVnc()
		self.state = self.getState()
		self.save()
		
	def getStartTasks(self):
		taskset = Device.getStartTasks(self)
		create_bridges = tasks.Task("create-bridges", self._createBridges, reverseFn=self._fallbackStop)
		start_vm = tasks.Task("start-vm", self._startVm, reverseFn=self._fallbackStop, after=create_bridges)
		for iface in self.interfaceSetAll():
			taskset.add(tasks.Task("start-interface-%s" % iface, self._startIface, args=(iface,), reverseFn=self._fallbackStop, after=start_vm))
		assign_vnc_port = tasks.Task("assign-vnc-port", self._assignVncPort, reverseFn=self._fallbackStop)
		start_vnc = tasks.Task("start-vnc", self._startVnc, reverseFn=self._fallbackStop, after=[start_vm, assign_vnc_port])
		taskset.add([create_bridges, start_vm, assign_vnc_port, start_vnc])
		return self._adaptTaskset(taskset)

	def _stopVnc(self):
		if not self.host or not self.getVncPort():
			return
		repy.stopVnc(self.host, self.id, self.getVncPort())
		self.host.giveId("port", self.getVncPort())
		self.setVncPort(None)
	
	def _stopVm(self):
		repy.stop(self.host, self.id)

	def getStopTasks(self):
		taskset = Device.getStopTasks(self)
		stop_vnc = tasks.Task("stop-vnc", self._stopVnc, reverseFn=self._fallbackStop)
		stop_vm = tasks.Task("stop-vm", self._stopVm, reverseFn=self._fallbackStop)
		unassign_vnc_port = tasks.Task("unassign-vnc-port", self._unassignVncPort, reverseFn=self._fallbackStop, after=stop_vnc)
		taskset.add([stop_vnc, stop_vm, unassign_vnc_port])
		return self._adaptTaskset(taskset)

	def _assignTemplate(self):
		self.setTemplate(templates.findName(self.type, self.getTemplate()))
		fault.check(self.getTemplate() and self.getTemplate() != "None", "Template not found")

	def _unassignHost(self):
		self.host = None
		self.save()

	def _assignHost(self):
		if not self.host:
			self.host = self.hostOptions().best()
			fault.check(self.host, "No matching host found")
			self.save()

	def _assignVncPort(self):
		assert self.host
		if not self.getVncPort():
			self.host.takeId("port", self.setVncPort)

	def _createVm(self):
		repy.create(self.host, self.id, self.getTemplate())

	def _fallbackDestroy(self):
		self._fallbackStop()
		if self.host:
			if self.state == State.PREPARED:
				self._destroyVm()
		self.state = self.getState()
		self.save()

	def getPrepareTasks(self):
		taskset = Device.getPrepareTasks(self)
		assign_template = tasks.Task("assign-template", self._assignTemplate, reverseFn=self._fallbackDestroy)
		assign_host = tasks.Task("assign-host", self._assignHost, reverseFn=self._fallbackDestroy)
		create_vm = tasks.Task("create-vm", self._createVm, reverseFn=self._fallbackDestroy, after=assign_host)
		taskset.add([assign_template, assign_host, create_vm])
		return self._adaptTaskset(taskset)

	def _unassignVncPort(self):
		if self.vnc_port and self.host:
			self.host.giveId("port", self.vnc_port)
		self.setVncPort(None)

	def _destroyVm(self):
		if self.host:
			repy.destroy(self.host, self.id)

	def getDestroyTasks(self):
		taskset = Device.getDestroyTasks(self)
		destroy_vm = tasks.Task("destroy-vm", self._destroyVm, reverseFn=self._fallbackDestroy)
		unassign_host = tasks.Task("unassign-host", self._unassignHost, after=destroy_vm, reverseFn=self._fallbackDestroy)
		taskset.add([destroy_vm, unassign_host])
		return self._adaptTaskset(taskset)

	def configure(self, properties):
		if "template" in properties:
			fault.check(self.state == State.CREATED, "Cannot change template of prepared device: %s" % self.name)
		if "args" in properties:
			fault.check(self.state != State.STARTED, "Cannot change arguments of running device: %s" % self.name)
		Device.configure(self, properties)
		if "template" in properties:
			self.setTemplate(properties["template"])
			self._assignTemplate()
		if "args" in properties:
			self.setArgs(properties["args"])
			self._assignTemplate()
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

	def downloadImageUri(self):
		assert self.state == State.PREPARED, "Download not supported"
		filename = "%s_%s.repy" % (self.topology.name, self.name)
		file = hostserver.randomFilename(self.host)
		repy.copyImage(self.host, self.id, file)
		return hostserver.downloadGrant(self.host, file, filename)

	def getResourceUsage(self):
		disk = 0
		memory = 0
		ports = 1 if self.state == State.STARTED else 0		
		if self.host:
			disk = repy.getDiskUsage(self.host, self.id)
			memory = repy.getMemoryUsage(self.host, self.id)
		return {"disk": disk, "memory": memory, "ports": ports}		

	def getIdUsage(self, host):
		ids = Device.getIdUsage(self, host)
		if self.vnc_port and self.host == host:
			ids["port"] = ids.get("port", set()) | set((self.vnc_port,))
		return ids

	def interfaceDevice(self, iface):
		return repy.interfaceDevice(self.id, iface.name)

	def toDict(self, auth):
		res = Device.toDict(self, auth)
		res["attrs"].update(vnc_port=self.getVncPort(), template=self.getTemplate(), args=self.getArgs())
		if auth:
			res["attrs"].update(vnc_password = self.vncPassword())
		return res				