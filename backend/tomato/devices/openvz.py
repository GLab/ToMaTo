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

from tomato.lib import util, vzctl, ifaceutil, hostserver, tasks, db, exceptions

class OpenVZDevice(common.TemplateMixin, common.VMIDMixin, common.VNCMixin, Device):

	vmid = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	vnc_port = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	template = models.CharField(max_length=255, null=True, validators=[db.templateValidator])

	class Meta:
		db_table = "tomato_openvzdevice"
		app_label = 'tomato'

	def upcast(self):
		return self

	def init(self):
		self.attrs = {}
		self.setAttribute("root_password", "glabroot", save=False)

	def setRootPassword(self, value):
		self.setAttribute("root_password", value)

	def getRootPassword(self):
		return self.getAttribute("root_password")

	def getState(self):
		if not self.getVmid() or not self.host:
			return State.CREATED
		return vzctl.getState(self.host, self.getVmid()) 

	def execute(self, cmd):
		#not asserting state==Started because this is called during startup
		try:
			return vzctl.execute(self.host, self.getVmid(), cmd)
		except exceptions.CommandError, exc:
			raise exceptions.CommandError(self.name, cmd, exc.errorCode, exc.errorMessage)

	def getCapabilities(self, user):
		capabilities = Device.getCapabilities(self, user)
		isUser = self.topology.checkAccess(Permission.ROLE_USER, user)
		capabilities["configure"].update({
			"template": self.state == State.CREATED,
			"root_password": True,
			"gateway4": True,
			"gateway6": True,
		})
		capabilities["action"].update({
			"execute": isUser and self.state == State.STARTED,
		})
		capabilities.update(other={
			"console": isUser and self.getVncPort() and self.state == State.STARTED
		})
		return capabilities

	def _runAction(self, action, attrs, direct):
		if action == "execute":
			fault.check("cmd" in attrs, "Command not given")
			try:
				return self.execute(attrs["cmd"])
			except exceptions.CommandError, exc:
				raise fault.new(str(exc), fault.USER_ERROR)
		else:
			return Device._runAction(self, action, attrs, direct)

	def _startVnc(self):
		vzctl.startVnc(self.host, self.getVmid(), self.getVncPort(), self.vncPassword())

	def _configureRoutes(self):
		#Note: usage of self as host is intentional
		ifaceutil.deleteDefaultRoute(self)
		if self.hasAttribute("gateway4"):
			ifaceutil.addDefaultRoute(self, self.getAttribute("gateway4"))
		if self.hasAttribute("gateway6"):
			ifaceutil.addDefaultRoute(self, self.getAttribute("gateway6"))

	def connectToBridge(self, iface, bridge):
		ifaceutil.bridgeCreate(self.host, bridge)
		ifaceutil.bridgeConnect(self.host, bridge, self.interfaceDevice(iface))
		ifaceutil.ifup(self.host, bridge)

	def _startDev(self):
		host = self.host
		vmid = self.getVmid()
		state = vzctl.getState(host, vmid)
		if not self.getVncPort():
			self._assignVncPort()
		if state == State.CREATED:
			self._prepareDev()
			state = vzctl.getState(host, vmid)
		for iface in self.interfaceSetAll():
			bridge = self.getBridge(iface)
			assert bridge, "Interface has no bridge %s" % iface
			ifaceutil.bridgeCreate(self.host, bridge)
			ifaceutil.ifup(self.host, bridge)
		try: 
			if state == State.PREPARED:
				vzctl.start(host, vmid)
			for iface in self.interfaceSetAll():
				assert ifaceutil.interfaceExists(host, self.interfaceDevice(iface))
				self.connectToBridge(iface, self.getBridge(iface))
				iface.upcast()._configureNetwork()
			self._startVnc()
			self.state = State.STARTED
			self.save()
		except:
			try:
				vzctl.stop(host, vmid)
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
		vzctl.stopVnc(self.host, self.getVmid(), self.getVncPort())
		self._unassignVncPort()
	
	def _stopVm(self):
		vzctl.stop(self.host, self.getVmid())

	def _stopDev(self):
		host = self.host
		vmid = self.getVmid()
		state = vzctl.getState(host, vmid)
		if state == State.STARTED:
			vzctl.stop(host, vmid)
			state = vzctl.getState(host, vmid)
		self.state = State.PREPARED
		self.save()
		if self.getVncPort():
			vzctl.stopVnc(host, vmid, self.getVncPort())
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

	def _configureVm(self):
		if self.getRootPassword():
			vzctl.setUserPassword(self.host, self.getVmid(), self.getRootPassword(), username="root")
		vzctl.setHostname(self.host, self.getVmid(), "%s-%s" % (self.topology.name.replace("_","-"), self.name ))

	def _prepareDev(self):
		#assign host
		self._assignHost()
		host = self.host
		
		self._assignBridges()
		
		self._assignVmid()
		fault.check(self.getVmid(), "No free vmid")
		vmid = self.getVmid()
		
		state = vzctl.getState(host, vmid)
		if state == State.STARTED:
			vzctl.stop(host, vmid)
			state = vzctl.getState(host, vmid)
		if state == State.PREPARED:
			self.state = vzctl.getState(host, vmid)
			self.save()
			return
		assert state == State.CREATED
		
		#nothing happened until here
		
		vzctl.create(host, vmid, self.getTemplate())
		try:
			self._configureVm()
			for iface in self.interfaceSetAll():
				vzctl.addInterface(host, vmid, iface.name)
			self.state = State.PREPARED
			self.save()
		except:
			try:
				vzctl.destroy(host, vmid)
			except:
				pass
			raise
	
	def getPrepareTasks(self):
		taskset = Device.getPrepareTasks(self)
		taskset.add(tasks.Task("prepare", self._prepareDev))
		return taskset

	def _destroyVm(self):
		if self.host:
			vzctl.destroy(self.host, self.getVmid())

	def _destroyDev(self):
		host = self.host
		vmid = self.getVmid()
		if not host:
			return
		if vmid:
			state = vzctl.getState(host, vmid)
			if state == State.STARTED:
				vzctl.stop(host, vmid)
				state = vzctl.getState(host, vmid)
			if state == State.PREPARED:
				vzctl.destroy(host, vmid)
				state = vzctl.getState(host, vmid)
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
		if "root_password" in properties:
			self.setRootPassword(properties["root_password"])
			if self.state == State.PREPARED or self.state == State.STARTED:
				vzctl.setUserPassword(self.host, self.getVmid(), self.getRootPassword(), username="root")
		if "gateway4" in properties:
			self.setAttribute("gateway4", properties["gateway4"])
			if self.state == State.STARTED:
				self._configureRoutes()
		if "gateway6" in properties:
			self.setAttribute("gateway6", properties["gateway6"])
			if self.state == State.STARTED:
				self._configureRoutes()
		if "template" in properties:
			self.setTemplate(properties["template"])
			fault.check(self.getTemplate(), "Template not found: %s" % properties["template"])
		self.save()

	def interfacesAdd(self, name, properties):
		fault.check(self.state != State.STARTED, "OpenVZ does not support adding interfaces to running VMs: %s" % self.name)
		import re
		fault.check(re.match("eth(\d+)", name), "Invalid interface name: %s" % name)
		try:
			fault.check(not self.interfaceSetGet(name), "Duplicate interface name: %s" % name)
		except Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface = ConfiguredInterface()
		iface.name = name
		iface.device = self
		iface.init()
		if self.state == State.PREPARED or self.state == State.STARTED:
			vzctl.addInterface(self.host, self.getVmid(), iface.name)
		iface.configure(properties)
		iface.save()
		Device.interfaceSetAdd(self, iface)

	def interfacesConfigure(self, name, properties):
		iface = self.interfaceSetGet(name).upcast()
		iface.configure(properties)

	def interfacesRename(self, name, properties):
		iface = self.interfaceSetGet(name).upcast()
		if self.state == State.PREPARED or self.state == State.STARTED:
			vzctl.deleteInterface(self.host, self.getVmid(), iface.name)
		try:
			fault.check(not self.interfaceSetGet(properties["name"]), "Duplicate interface name: %s" % properties["name"])
		except Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface.name = properties["name"]
		if self.state == State.PREPARED or self.state == State.STARTED:
			vzctl.addInterface(self.host, self.getVmid(), iface.name)
		if self.state == State.STARTED:
			self.connectToBridge(iface, self.getBridge(iface))
			iface._configureNetwork()
		iface.save()

	def interfacesDelete(self, name):
		iface = self.interfaceSetGet(name).upcast()
		if iface.isConnected():
			iface.connection.connector.upcast().connectionsDelete(unicode(iface))
		if self.state == State.PREPARED or self.state == State.STARTED:
			vzctl.deleteInterface(self.host, self.getVmid(), iface.name)
		iface.delete()

	def migrateRun(self, host=None):
		if self.state == State.CREATED:
			self._unassignHost()
			self._unassignVmid()
			return
		task = tasks.get_current_task()
		#save src data
		src_host = self.host
		src_vmid = resources.get(self, self.VMID_SLOT)
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
		try:
			vzctl.migrate(src_host, src_vmid.num, dst_host, dst_vmid.num, self.getTemplate(), ifaces)
		except:
			# reverted to SRC host
			if self.state == State.STARTED:
				self._assignVncPort()
				self._startVnc()
			raise
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
			self._assignVncPort()
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
				if self.state == State.STARTED:
					self.connectToBridge(iface, self.getBridge(iface))

	def checkUploadedImage(self, path):
		error = vzctl.checkImage(self.host, path)
		if error:
			raise fault.new("Invalid OpenVZ image: %s" % error, fault.USER_ERROR)
				
	def useUploadedImageRun(self, path):
		assert self.state == State.PREPARED, "Upload not supported"
		vzctl.useImage(self.host, self.getVmid(), path, forceGzip=True)

	def downloadImageUri(self):
		assert self.state == State.PREPARED, "Download not supported"
		filename = "%s_%s.tar.gz" % (self.topology.name, self.name)
		file = self.host.getHostServer().randomFilename()
		vzctl.copyImage(self.host, self.getVmid(), file, forceGzip=True)
		return self.host.getHostServer().downloadGrant(file, filename)

	def getResourceUsage(self):
		disk = 0
		memory = 0
		ports = 1 if self.state == State.STARTED else 0		
		if self.host and self.getVmid():
			disk = vzctl.getDiskUsage(self.host, self.getVmid())
			memory = vzctl.getMemoryUsage(self.host, self.getVmid())
		traffic = 0
		if self.state == State.STARTED:
			for iface in self.interfaceSetAll():
				dev = self.interfaceDevice(iface)
				traffic += ifaceutil.getRxBytes(self.host, dev)
				traffic += ifaceutil.getTxBytes(self.host, dev)
		return {"disk": disk, "memory": memory, "ports": ports, "traffic": traffic}		

	def interfaceDevice(self, iface):
		return vzctl.interfaceDevice(self.getVmid(), iface.name)

	def toDict(self, auth):
		res = Device.toDict(self, auth)
		res["attrs"].update(vnc_port=self.getVncPort(), template=self.getConfiguredTemplate(),
			gateway4=self.getAttribute("gateway4"), gateway6=self.getAttribute("gateway6"))
		if auth:
			res["attrs"].update(root_password=self.getRootPassword(), vnc_password = self.vncPassword())
		return res


class ConfiguredInterface(Interface):

	class Meta:
		db_table = "tomato_configuredinterface"
		app_label = 'tomato'
	
	def init(self):
		self.attrs = {}		
		self.setAttribute("use_dhcp", False, save=False)
	
	def upcast(self):
		return self

	def getCapabilities(self, user):
		capabilities = Interface.getCapabilities(self, user)
		capabilities["configure"].update({
			"use_dhcp": True,
			"ip4address": True,
			"ip6address": True,
		})
		return capabilities

	def interfaceName(self):
		return self.device.upcast().interfaceDevice(self)
		
	def configure(self, properties):
		Interface.configure(self, properties)
		changed=False
		if "use_dhcp" in properties:
			self.setAttribute("use_dhcp", properties["use_dhcp"])
			changed = True
		if "ip4address" in properties:
			self.setAttribute("ip4address", properties["ip4address"])
			changed = True
		if "ip6address" in properties:
			self.setAttribute("ip6address", properties["ip6address"])
			changed = True
		if changed:
			if self.device.state == State.STARTED:
				self._configureNetwork()
			self.save()
			
	def _configureNetwork(self):
		dev = self.device.upcast()
		#Note usage of dev instead of host is intentional
		if self.hasAttribute("ip4address"):
			ifaceutil.addAddress(dev, self.name, self.getAttribute("ip4address"))
			ifaceutil.ifup(dev, self.name) 
		if self.hasAttribute("ip6address"):
			ifaceutil.addAddress(dev, self.name, self.getAttribute("ip6address"))
			ifaceutil.ifup(dev, self.name) 
		if self.hasAttribute("use_dhcp") and util.parse_bool(self.getAttribute("use_dhcp")):
			ifaceutil.startDhcp(dev, self.name)
			
	def toDict(self, auth):
		res = Interface.toDict(self, auth)
		res["attrs"].update(ip4address=self.getAttribute("ip4address"), ip6address=self.getAttribute("ip6address"),
			use_dhcp=self.getAttribute("use_dhcp"))	
		return res				