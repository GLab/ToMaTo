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

from tomato.devices import Device, Interface, common
from tomato import fault, config
from tomato.hosts import templates, resources
from tomato.generic import State
from tomato.lib import qm, hostserver, tasks, ifaceutil, db
from tomato.topology import Permission

import hashlib, re
from django.db import models

class KVMDevice(common.TemplateMixin, common.VMIDMixin, common.VNCMixin, Device):
	
	vmid = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	vnc_port = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	template = models.CharField(max_length=255, null=True, validators=[db.templateValidator])
	
	class Meta:
		db_table = "tomato_kvmdevice"
		app_label = 'tomato'

	def upcast(self):
		return self

	def init(self):
		self.attrs = {}

	def sendKeys(self, keycodes):
		#not asserting state==Started because this is called during startup
		qm.sendKeys(self.host, self.getVmid(), keycodes)

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
		file = self.host.getHostServer().randomFilename()
		qm.copyImage(self.host, self.getVmid(), file)
		return self.host.getHostServer().downloadGrant(file, filename)

	def checkUploadedImage(self, path):
		error = qm.checkImage(self.host, path)
		if error:
			raise fault.new("Invalid KVM image: %s" % error, fault.USER_ERROR)

	def useUploadedImageRun(self, path):
		assert self.state == State.PREPARED, "Upload not supported"
		qm.useImage(self.host, self.getVmid(), path, move=True)

	def _startVnc(self):
		if not self.getVncPort():
			self._assignVncPort()
		qm.startVnc(self.host, self.getVmid(), self.getVncPort(), self.vncPassword())

	def connectToBridge(self, iface, bridge):
		ifaceutil.bridgeCreate(self.host, bridge)
		ifaceutil.bridgeConnect(self.host, bridge, self.interfaceDevice(iface))
		ifaceutil.ifup(self.host, bridge)

	def _startDev(self):
		host = self.host
		vmid = self.getVmid()
		state = qm.getState(host, vmid)
		if not self.getVncPort():
			self._assignVncPort()
		if state == State.CREATED:
			self._prepareDev()
			state = qm.getState(host, vmid)
		for iface in self.interfaceSetAll():
			iface_id = int(re.match("eth(\d+)", iface.name).group(1))
			# qm automatically connects ethN to vmbrN
			# if this bridge does not exist, kvm start fails
			ifaceutil.bridgeCreate(host, "vmbr%d" % iface_id)
		try: 
			if state == State.PREPARED:
				qm.start(host, vmid)
			for iface in self.interfaceSetAll():
				qm.waitForInterface(host, vmid, iface.name)
				self.connectToBridge(iface, self.getBridge(iface))
			self._startVnc()
			self.state = State.STARTED
			self.save()
		except:
			try:
				qm.stop(host, vmid)
			except:
				pass
			raise

	def getStartTasks(self):
		taskset = Device.getStartTasks(self)
		taskset.add(tasks.Task("start", self._startDev))
		return taskset

	def _stopVnc(self):
		if not self.host or not self.getVmid() or not self.getVncPort():
			return
		qm.stopVnc(self.host, self.getVmid(), self.getVncPort())
	
	def _stopDev(self):
		host = self.host
		vmid = self.getVmid()
		state = self.getState()
		if state == State.STARTED:
			qm.stop(host, vmid)
			state = self.getState()
		self.state = State.PREPARED
		self.save()
		if self.getVncPort():
			qm.stopVnc(host, vmid, self.getVncPort())
			self._unassignVncPort()
	
	def getStopTasks(self):
		taskset = Device.getStopTasks(self)
		taskset.add(tasks.Task("stop", self._stopDev))
		return taskset

	def _configureVm(self):
		qm.setName(self.host, self.getVmid(), "%s_%s" % (self.topology.name, self.name))
	
	def _assignHost(self):
		#assign host
		if not self.host:
			self.host = self.hostOptions().best()
			fault.check(self.host, "No matching host found")
			self.save()		
			
	
	def _prepareDev(self):
		self._assignHost()
		host = self.host
		
		self._assignBridges()
		
		self._assignVmid()
		fault.check(self.getVmid(), "No free vmid")
		vmid = self.getVmid()
		
		state = qm.getState(host, vmid)
		if state == State.STARTED:
			qm.stop(host, vmid)
			state = qm.getState(host, vmid)
		if state == State.PREPARED:
			qm.destroy(host, vmid)
			state = qm.getState(host, vmid)
		assert state == State.CREATED
		
		#nothing happened until here
		
		qm.create(host, vmid)
		try:
			qm.useTemplate(host, vmid, self.getTemplate())
			self._configureVm()
			for iface in self.interfaceSetAll():
				qm.addInterface(host, vmid, iface.name)
			self.state = State.PREPARED
			self.save()
		except:
			try:
				qm.destroy(host, vmid)
			except:
				pass
			raise
		
	def getPrepareTasks(self):
		taskset = Device.getPrepareTasks(self)
		taskset.add(tasks.Task("prepare", self._prepareDev))
		return taskset

	def _unassignHost(self):
		self.host = None
		self.save()
		
	def _destroyDev(self):
		host = self.host
		vmid = self.getVmid()
		if not host:
			return
		if vmid:
			state = qm.getState(host, vmid)
			if state == State.STARTED:
				qm.stop(host, vmid)
				state = qm.getState(host, vmid)
			if state == State.PREPARED:
				qm.destroy(host, vmid)
				state = qm.getState(host, vmid)
			assert state == State.CREATED
			self.state = State.CREATED			
			self.save()
			self._unassignVmid()
		self._unassignBridges()
		self._unassignHost()
		
	def getDestroyTasks(self):
		taskset = Device.getDestroyTasks(self)
		taskset.add(tasks.Task("destroy", self._destroyDev))
		return taskset

	def configure(self, properties):
		if "template" in properties:
			fault.check(self.state == State.CREATED, "Cannot change template of prepared device: %s" % self.name)
		Device.configure(self, properties)
		if "template" in properties:
			self.setTemplate(properties["template"])
		self.save()
			
	def interfacesAdd(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		fault.check(self.state != State.STARTED, "Changes of running KVMs are not supported")
		fault.check(re.match("eth(\d+)", name), "Invalid interface name: %s" % name)
		iface = Interface()
		try:
			if self.interfaceSetGet(name):
				raise fault.new("Duplicate interface name: %s" % name, fault.USER_ERROR)
		except Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface.name = name
		iface.device = self
		iface.init()
		if self.state == State.PREPARED:
			qm.addInterface(self.host, self.getVmid(), iface.name)
		iface.save()
		self.interfaceSetAdd(iface)
		self.save()

	def interfacesConfigure(self, name, properties):
		pass
	
	def interfacesRename(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		fault.check(self.state != State.STARTED, "Changes of running KVMs are not supported")
		iface = self.interfaceSetGet(name)
		newName = properties["name"]
		fault.check(re.match("eth(\d+)", newName), "Invalid interface name: %s" % name)
		try:
			if self.interfaceSetGet(newName):
				raise fault.new("Duplicate interface name: %s" % newName, fault.USER_ERROR)
		except Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		if self.state == State.PREPARED:
			connector = None
			connectionAttributes = None
			if iface.isConnected():
				connector = iface.connection.connector
				connectionAttributes = iface.connection.upcast().toDict(None)["attrs"]
				connector.upcast().connectionsDelete(unicode(iface))
			qm.deleteInterface(self.host, self.getVmid(), iface.name)
		iface.name = newName
		iface.save()
		if self.state == State.PREPARED:
			qm.addInterface(self.host, self.getVmid(), iface.name)
			if connector:
				connector.upcast().connectionsAdd(unicode(iface), connectionAttributes)
		self.save()
	
	def interfacesDelete(self, name): #@UnusedVariable, pylint: disable-msg=W0613
		fault.check(self.state != State.STARTED, "Changes of running KVMs are not supported")
		iface = self.interfaceSetGet(name)
		if iface.isConnected():
			iface.connection.connector.upcast().connectionsDelete(unicode(iface))
		if self.state == State.PREPARED:
			qm.deleteInterface(self.host, self.getVmid(), iface.name)
		iface.delete()
		
	def getResourceUsage(self):
		traffic = 0
		disk = 0
		memory = 0
		ports = 1 if self.state == State.STARTED else 0		
		if self.host and self.getVmid():
			disk = qm.getDiskUsage(self.host, self.getVmid())
			memory = qm.getMemoryUsage(self.host, self.getVmid())
		if self.state == State.STARTED:
			for iface in self.interfaceSetAll():
				dev = self.interfaceDevice(iface)
				traffic += ifaceutil.getRxBytes(self.host, dev)
				traffic += ifaceutil.getTxBytes(self.host, dev)
		return {"disk": disk, "memory": memory, "ports": ports, "traffic": traffic}		
	
	def interfaceDevice(self, iface):
		try:
			return qm.interfaceDevice(self.host, self.getVmid(), iface.name)
		except:
			self.state = qm.getState(self.host, self.getVmid())
			self.save()
			raise

	def migrateRun(self, host=None):
		if self.state == State.CREATED:
			self._unassignVmid()
			self._unassignHost()
			return
		task = tasks.get_current_task()
		#save src data
		src_host = self.host
		src_vmid = self.vmid
		#assign new host and vmid
		self.host = None
		if host:
			self.host = host
		else:
			self._assignHost()
		dst_host = self.host
		dst_vmid = resources.take(dst_host, "vmid", self, "migration")
		#reassign host and vmid
		self.host = src_host
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
			try:
				self.state = State.PREPARED
				for iface in self.interfaceSetAll():
					if iface.isConnected():
						con = iface.connection.upcast()
						con.destroyBridge()
			finally:
				self.state = State.STARTED			
		ifaces = map(lambda x: x.name, self.interfaceSetAll())
		qm.migrate(src_host, src_vmid.num, dst_host, dst_vmid.num, ifaces)
		#switch host and vmid
		self.host = dst_host
		self.vmid = dst_vmid
		self.save()
		resources.give(self, self.VMID_SLOT)
		self.vmid.slot = self.VMID_SLOT
		self.vmid.save()
		self.save()
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
		res["attrs"].update(template=self.getConfiguredTemplate())
		if auth:
			res["attrs"].update(vnc_password=self.vncPassword(), vnc_port=self.getVncPort())
		return res

