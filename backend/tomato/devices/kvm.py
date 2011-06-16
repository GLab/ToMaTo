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

from tomato.devices import Device, Interface
from tomato import fault, config
from tomato.hosts import templates
from tomato.generic import State
from tomato.lib import qm, hostserver, tasks, ifaceutil, db
from tomato.topology import Permission

import hashlib, re
from django.db import models

class KVMDevice(Device):
	
	vmid = models.PositiveIntegerField(null=True)
	vnc_port = models.PositiveIntegerField(null=True)
	template = models.CharField(max_length=255, null=True, validators=[db.templateValidator])
	
	class Meta:
		db_table = "tomato_kvmdevice"
		app_label = 'tomato'

	def upcast(self):
		return self

	def init(self):
		self.attrs = {}

	def setVmid(self, value):
		self.vmid = value
		self.save()

	def getVmid(self):
		return self.vmid

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

	def sendKeys(self, keycodes):
		#not asserting state==Started because this is called during startup
		return qm.sendKeys(self.host, self.getVmid(), keycodes)

	def getState(self):
		if not self.getVmid() or not self.host:
			return State.CREATED
		return qm.getState(self.host, self.getVmid()) 

	def getCapabilities(self, user):
		capabilities = Device.getCapabilities(self, user)
		isUser = self.topology.checkAccess(Permission.ROLE_USER, user)
		isManager = self.topology.checkAccess(Permission.ROLE_MANAGER, user)
		capabilities["configure"].update({
			"template": self.state == State.CREATED,
		})
		capabilities["action"].update({
			"send_keys": isUser and self.state == State.STARTED,
		})
		capabilities.update(other={
			"console": isUser and self.getVncPort() and self.state == State.STARTED
		})
		return capabilities

	def _runAction(self, action, attrs, direct):
		if action == "send_keys":
			return self.sendKeys(attrs["keycodes"])
		else:
			return Device._runAction(self, action, attrs, direct)

	def downloadImageUri(self):
		assert self.state == State.PREPARED, "Download not supported"
		filename = "%s_%s.qcow2" % (self.topology.name, self.name)
		file = hostserver.randomFilename(self.host)
		qm.copyImage(self.host, self.getVmid(), file)
		return hostserver.downloadGrant(self.host, file, filename)

	def useUploadedImageRun(self, path):
		assert self.state == State.PREPARED, "Upload not supported"
		qm.useImage(self.host, self.getVmid(), path, move=True)

	def _startVnc(self):
		if not self.getVncPort():
			self.setVncPort(self.host.nextFreePort())
		qm.startVnc(self.host, self.getVmid(), self.getVncPort(), self.vncPassword())

	def _startIface(self, iface):
		bridge = self.bridgeName(iface)
		ifaceutil.bridgeCreate(self.host, bridge)
		ifaceutil.bridgeConnect(self.host, bridge, self.interfaceDevice(iface))
		ifaceutil.ifup(self.host, bridge)

	def _startVm(self):
		for iface in self.interfaceSetAll():
			iface_id = int(re.match("eth(\d+)", iface.name).group(1))
			# qm automatically connects ethN to vmbrN
			# if this bridge does not exist, kvm start fails
			if not ifaceutil.interfaceExists(self.host, "vmbr%d" % iface_id):
				ifaceutil.bridgeCreate(self.host, "vmbr%d" % iface_id)
		qm.start(self.host, self.getVmid())

	def getStartTasks(self):
		taskset = Device.getStartTasks(self)
		start_vm = tasks.Task("start-vm", self._startVm, reverseFn=self._fallbackStop)
		for iface in self.interfaceSetAll():
			taskset.add(tasks.Task("start-interface-%s" % iface, self._startIface, args=(iface,), reverseFn=self._fallbackStop, after=start_vm))
		assign_vnc_port = tasks.Task("assign-vnc-port", self._assignVncPort, reverseFn=self._fallbackStop)
		start_vnc = tasks.Task("start-vnc", self._startVnc, reverseFn=self._fallbackStop, after=[start_vm, assign_vnc_port])
		taskset.add([start_vm, assign_vnc_port, start_vnc])
		return taskset

	def _stopVnc(self):
		qm.stopVnc(self.host, self.getVmid(), self.getVncPort())
	
	def _stopVm(self):
		qm.stop(self.host, self.getVmid())

	def _fallbackStop(self):
		self.state = self.getState()
		self.save()
		if self.state == State.STARTED:
			self._stopVm()
		if self.getVncPort():
			if qm.vncRunning(self.host, self.getVmid(), self.getVncPort()):
				self._stopVnc()
			self._unassignVncPort()
		self.state = self.getState()
		self.save()
	
	def getStopTasks(self):
		taskset = Device.getStopTasks(self)
		stop_vm = tasks.Task("stop-vm", self._stopVm, reverseFn=self._fallbackStop)
		stop_vnc = tasks.Task("stop-vnc", self._stopVnc, reverseFn=self._fallbackStop)
		unassign_vnc_port = tasks.Task("unassign-vnc-port", self._unassignVncPort, reverseFn=self._fallbackStop, after=stop_vnc)
		taskset.add([stop_vm, stop_vnc, unassign_vnc_port])
		return taskset

	def _assignTemplate(self):
		self.setTemplate(templates.findName(self.type, self.getTemplate()))
		fault.check(self.getTemplate() and self.getTemplate() != "None", "Template not found")

	def _assignHost(self):
		if not self.host:
			self.host = self.hostOptions().best()
			fault.check(self.host, "No matching host found")
			self.save()

	def _assignVmid(self):
		assert self.host
		if not self.getVmid():
			self.host.takeId("vmid", self.setVmid)

	def _assignVncPort(self):
		assert self.host
		if not self.getVncPort():
			self.host.takeId("port", self.setVncPort)

	def _useTemplate(self):
		qm.useTemplate(self.host, self.getVmid(), self.getTemplate())

	def _configureVm(self):
		qm.setName(self.host, self.getVmid(), "%s_%s" % (self.topology.name, self.name))

	def _createIface(self, iface):
		qm.addInterface(self.host, self.getVmid(), iface.name)
	
	def _createVm(self):
		qm.create(self.host, self.getVmid())

	def _fallbackDestroy(self):
		self._fallbackStop()
		if self.host and self.getVmid():
			if self.getState() == State.PREPARED:
				self._destroyVm()
		self.state = self.getState()
		self.save()

	def getPrepareTasks(self):
		taskset = Device.getPrepareTasks(self)
		assign_template = tasks.Task("assign-template", self._assignTemplate)
		assign_host = tasks.Task("assign-host", self._assignHost)
		assign_vmid = tasks.Task("assign-vmid", self._assignVmid, after=assign_host)
		create_vm = tasks.Task("create-vm", self._createVm, reverseFn=self._fallbackDestroy, after=assign_vmid)
		use_template = tasks.Task("use-template", self._useTemplate, reverseFn=self._fallbackDestroy, after=create_vm)
		configure_vm = tasks.Task("configure-vm", self._configureVm, reverseFn=self._fallbackDestroy, after=create_vm)
		for iface in self.interfaceSetAll():
			taskset.add(tasks.Task("create-interface-%s" % iface.name, self._createIface, args=(iface,), reverseFn=self._fallbackDestroy, after=create_vm))
		taskset.add([assign_template, assign_host, assign_vmid, create_vm, use_template, configure_vm])
		return taskset

	def _unassignHost(self):
		self.host = None
		self.save()
		
	def _unassignVmid(self):
		if self.vmid and self.host:
			self.host.giveId("vmid", self.vmid)
		self.setVmid(None)

	def _unassignVncPort(self):
		if self.vnc_port:
			self.host.giveId("port", self.vnc_port)
		self.setVncPort(None)

	def _destroyVm(self):
		if self.host and self.getVmid():
			qm.destroy(self.host, self.getVmid())

	def getDestroyTasks(self):
		taskset = Device.getDestroyTasks(self)
		destroy_vm = tasks.Task("destroy-vm", self._destroyVm, reverseFn=self._fallbackDestroy)
		unassign_vmid = tasks.Task("unassign-vmid", self._unassignVmid, reverseFn=self._fallbackDestroy, after=destroy_vm)
		unassign_host = tasks.Task("unassign-host", self._unassignHost, reverseFn=self._fallbackDestroy, after=unassign_vmid)
		taskset.add([destroy_vm, unassign_host, unassign_vmid])
		return taskset

	def configure(self, properties):
		if "template" in properties:
			fault.check(self.state == State.CREATED, "Cannot change template of prepared device: %s" % self.name)
		Device.configure(self, properties)
		if "template" in properties:
			self._assignTemplate()
		self.save()
			
	def interfacesAdd(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		fault.check(self.state != State.STARTED, "Changes of running KVMs are not supported")
		fault.check(re.match("eth(\d+)", name), "Invalid interface name: %s" % name)
		iface = Interface()
		try:
			if self.interfaceSetGet(name):
				raise fault.new("Duplicate interface name: %s" % name)
		except Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface.name = name
		iface.device = self
		iface.init()
		if self.state == State.PREPARED:
			qm.addInterface(self.host, self.getVmid(), iface.name)
		iface.save()
		Device.interfaceSetAdd(self, iface)

	def interfacesConfigure(self, name, properties):
		pass
	
	def interfacesRename(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		#FIXME: implement by delete-add
		fault.check(False, "KVM does not support renaming interfaces: %s" % name)
	
	def interfacesDelete(self, name): #@UnusedVariable, pylint: disable-msg=W0613
		fault.check(self.state != State.STARTED, "Changes of running KVMs are not supported")
		iface = self.interfaceSetGet(name)
		if self.state == State.PREPARED:
			qm.deleteInterface(self.host, self.getVmid(), iface.name)
		iface.delete()
		
	def vncPassword(self):
		if not self.getVmid():
			return "---"
		m = hashlib.md5()
		m.update(config.PASSWORD_SALT)
		m.update(str(self.name))
		m.update(str(self.getVmid()))
		m.update(str(self.getVncPort()))
		m.update(str(self.topology.owner))
		return m.hexdigest()

	def getResourceUsage(self):
		disk = 0
		memory = 0
		ports = 1 if self.state == State.STARTED else 0		
		if self.host and self.getVmid():
			disk = qm.getDiskUsage(self.host, self.getVmid())
			memory = qm.getMemoryUsage(self.host, self.getVmid())
		return {"disk": disk, "memory": memory, "ports": ports}		
	
	def getIdUsage(self, host):
		ids = Device.getIdUsage(self, host)
		if self.vnc_port and self.host == host:
			ids["port"] = ids.get("port", set()) | set((self.vnc_port,))
		if self.vmid and self.host == host:
			ids["vmid"] = ids.get("vmid", set()) | set((self.vmid,))
		if self.hasAttribute("migration"):
			migration = self.getAttribute("migration")
			if host.name in migration:
				ids["vmid"] |= set((migration[host.name],))
		return ids
	
	def interfaceDevice(self, iface):
		return qm.interfaceDevice(self.host, self.getVmid(), iface.name)

	def migrateRun(self, host=None):
		if self.state == State.CREATED:
			self._unassignVmid()
			self._unassignHost()
			return
		task = tasks.get_current_task()
		#save src data
		src_host = self.host
		src_vmid = self.getVmid()
		self.setAttribute("migration", {src_host.name: src_vmid})
		#assign new host and vmid
		self.host = None
		self.setVmid(None)
		if host:
			self.host = host
		else:
			self._assignHost()
		self._assignVmid()
		dst_host = self.host
		dst_vmid = self.getVmid()
		self.setAttribute("migration", {src_host.name: src_vmid, dst_host.name: dst_vmid})
		#reassign host and vmid
		self.host = src_host
		self.setVmid(src_vmid)
		#destroy all connectors and save their state
		constates={}
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector.upcast()
				if con.name in constates:
					continue
				constates[con.name] = con.state
				if con.state == State.STARTED:
					con.stop(True, noProcess=True)
				if con.state == State.PREPARED:
					con.destroy(True, noProcess=True)
		tasks.set_current_task(task)
		#actually migrate the vm
		if self.state == State.STARTED:
			self._stopVnc()
		ifaces = map(lambda x: x.name, self.interfaceSetAll())
		qm.migrate(src_host, src_vmid, dst_host, dst_vmid, ifaces)
		#switch host and vmid
		self.host = dst_host
		self.setVmid(dst_vmid)
		src_host.giveId("vmid", src_vmid)
		self.save()
		self.deleteAttribute("migration")
		self._configureVm()
		if self.state == State.STARTED:
			self._startVnc()
		#redeploy all connectors
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector.upcast()
				if not con.name in constates:
					continue
				state = constates[con.name]
				del constates[con.name]
				if state == State.PREPARED or state == State.STARTED:
					con.prepare(True, noProcess=True)
				if state == State.STARTED:
					con.start(True, noProcess=True)

	def toDict(self, auth):
		res = Device.toDict(self, auth)
		res["attrs"].update(vmid=self.getVmid(), template=self.getTemplate())
		if auth:
			res["attrs"].update(vnc_password=self.vncPassword(), vnc_port=self.getVncPort())
		return res

