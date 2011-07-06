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

from tomato.lib import util, vzctl, ifaceutil, hostserver, tasks, db

class OpenVZDevice(Device):

	vmid = models.PositiveIntegerField(null=True)
	vnc_port = models.PositiveIntegerField(null=True)
	template = models.CharField(max_length=255, null=True, validators=[db.templateValidator])

	class Meta:
		db_table = "tomato_openvzdevice"
		app_label = 'tomato'

	def upcast(self):
		return self

	def init(self):
		self.attrs = {}
		self.setAttribute("root_password", "glabroot", save=False)

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
		return vzctl.execute(self.host, self.getVmid(), cmd)

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
			return self.execute(attrs["cmd"])
		else:
			return Device._runAction(self, action, attrs, direct)

	def vncPassword(self):
		if not self.getVncPort():
			return None 
		m = hashlib.md5()
		m.update(config.PASSWORD_SALT)
		m.update(str(self.name))
		m.update(str(self.getVmid()))
		m.update(str(self.getVncPort()))
		m.update(str(self.topology.owner))
		return m.hexdigest()
	
	def _startVnc(self):
		vzctl.startVnc(self.host, self.getVmid(), self.getVncPort(), self.vncPassword())

	def _startVm(self):
		vzctl.start(self.host, self.getVmid())

	def _checkInterfacesExist(self):
		for i in self.interfaceSetAll():
			assert ifaceutil.interfaceExists(self.host, self.interfaceDevice(i))

	def _createBridges(self):
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				bridge = self.getBridge(iface)
				assert bridge, "Interface has no bridge %s" % iface
				ifaceutil.bridgeCreate(self.host, bridge)
				ifaceutil.ifup(self.host, bridge)

	def _configureRoutes(self):
		#Note: usage of self as host is intentional
		ifaceutil.deleteDefaultRoute(self)
		if self.hasAttribute("gateway4"):
			ifaceutil.addDefaultRoute(self, self.getAttribute("gateway4"))
		if self.hasAttribute("gateway6"):
			ifaceutil.addDefaultRoute(self, self.getAttribute("gateway6"))

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
		check_interfaces_exist = tasks.Task("check-interfaces-exist", self._checkInterfacesExist, reverseFn=self._fallbackStop, after=start_vm)
		interfaces_configured = []
		for iface in self.interfaceSetAll():
			ts = iface.upcast().getStartTasks()
			ts.prefix(iface).after(check_interfaces_exist)
			interfaces_configured.append(ts)
			taskset.add(ts)
		configure_routes = tasks.Task("configure-routes", self._configureRoutes, reverseFn=self._fallbackStop, after=interfaces_configured)
		assign_vnc_port = tasks.Task("assign-vnc-port", self._assignVncPort, reverseFn=self._fallbackStop)
		start_vnc = tasks.Task("start-vnc", self._startVnc, reverseFn=self._fallbackStop, after=[start_vm, assign_vnc_port])
		taskset.add([create_bridges, start_vm, check_interfaces_exist, configure_routes, assign_vnc_port, start_vnc])
		return self._adaptTaskset(taskset)

	def _stopVnc(self):
		assert self.host and self.getVmid() and self.getVncPort()
		vzctl.stopVnc(self.host, self.getVmid(), self.getVncPort())
		self.host.giveId("port", self.getVncPort())
		self.setVncPort(None)
	
	def _stopVm(self):
		vzctl.stop(self.host, self.getVmid())

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

	def _assignVmid(self):
		assert self.host
		if not self.getVmid():
			self.host.takeId("vmid", self.setVmid)

	def _assignVncPort(self):
		assert self.host
		if not self.getVncPort():
			self.host.takeId("port", self.setVncPort)

	def _configureVm(self):
		if self.getRootPassword():
			vzctl.setUserPassword(self.host, self.getVmid(), self.getRootPassword(), username="root")
		vzctl.setHostname(self.host, self.getVmid(), "%s-%s" % (self.topology.name.replace("_","-"), self.name ))

	def _createInterfaces(self):
		for iface in self.interfaceSetAll():
			vzctl.addInterface(self.host, self.getVmid(), iface.name)

	def _createVm(self):
		vzctl.create(self.host, self.getVmid(), self.getTemplate())

	def _fallbackDestroy(self):
		self._fallbackStop()
		if self.host and self.getVmid():
			if self.state == State.PREPARED:
				self._destroyVm()
		self.state = self.getState()
		self.save()

	def getPrepareTasks(self):
		taskset = Device.getPrepareTasks(self)
		assign_template = tasks.Task("assign-template", self._assignTemplate, reverseFn=self._fallbackDestroy)
		assign_host = tasks.Task("assign-host", self._assignHost, reverseFn=self._fallbackDestroy)
		assign_vmid = tasks.Task("assign-vmid", self._assignVmid, reverseFn=self._fallbackDestroy, after=assign_host)
		create_vm = tasks.Task("create-vm", self._createVm, reverseFn=self._fallbackDestroy, after=assign_vmid)
		configure_vm = tasks.Task("configure-vm", self._configureVm, reverseFn=self._fallbackDestroy, after=create_vm)
		create_interfaces = tasks.Task("create-interfaces", self._createInterfaces, reverseFn=self._fallbackDestroy, after=configure_vm)
		taskset.add([assign_template, assign_host, assign_vmid, create_vm, configure_vm, create_interfaces])
		return self._adaptTaskset(taskset)

	def _unassignVmid(self):
		if self.vmid:
			self.host.giveId("vmid", self.vmid)
		self.setVmid(None)

	def _unassignVncPort(self):
		if self.vnc_port and self.host:
			self.host.giveId("port", self.vnc_port)
		self.setVncPort(None)

	def _destroyVm(self):
		if self.host:
			vzctl.destroy(self.host, self.getVmid())

	def getDestroyTasks(self):
		taskset = Device.getDestroyTasks(self)
		destroy_vm = tasks.Task("destroy-vm", self._destroyVm, reverseFn=self._fallbackDestroy)
		unassign_vmid = tasks.Task("unassign-vmid", self._unassignVmid, after=destroy_vm, reverseFn=self._fallbackDestroy)
		unassign_host = tasks.Task("unassign-host", self._unassignHost, after=unassign_vmid, reverseFn=self._fallbackDestroy)
		taskset.add([destroy_vm, unassign_host, unassign_vmid])
		return self._adaptTaskset(taskset)

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
			self._assignTemplate()
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
			iface.prepare_run()
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
		if self.state == State.STARTED:
			iface.connectToBridge()
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
			try:
				self.state = State.PREPARED
				self._triggerConnections()
			finally:
				self.state = State.STARTED
		ifaces = map(lambda x: x.name, self.interfaceSetAll())
		try:
			vzctl.migrate(src_host, src_vmid, dst_host, dst_vmid, self.getTemplate(), ifaces)
		except:
			# reverted to SRC host
			if self.state == State.STARTED:
				self._assignVncPort()
				self._startVnc()
			raise
		#switch host and vmid
		self.host = dst_host
		self.setVmid(dst_vmid)
		src_host.giveId("vmid", src_vmid)
		self.save()
		self.deleteAttribute("migration")
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
					iface.upcast().connectToBridge()
				
	def useUploadedImageRun(self, path):
		assert self.state == State.PREPARED, "Upload not supported"
		vzctl.useImage(self.host, self.getVmid(), path, forceGzip=True)

	def downloadImageUri(self):
		assert self.state == State.PREPARED, "Download not supported"
		filename = "%s_%s.tar.gz" % (self.topology.name, self.name)
		file = hostserver.randomFilename(self.host)
		vzctl.copyImage(self.host, self.getVmid(), file, forceGzip=True)
		return hostserver.downloadGrant(self.host, file, filename)

	def getResourceUsage(self):
		disk = 0
		memory = 0
		ports = 1 if self.state == State.STARTED else 0		
		if self.host and self.getVmid():
			disk = vzctl.getDiskUsage(self.host, self.getVmid())
			memory = vzctl.getMemoryUsage(self.host, self.getVmid())
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
		return vzctl.interfaceDevice(self.getVmid(), iface.name)

	def toDict(self, auth):
		res = Device.toDict(self, auth)
		res["attrs"].update(vmid=self.getVmid(), vnc_port=self.getVncPort(), template=self.getTemplate(),
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

	def connectToBridge(self):
		dev = self.device.upcast()
		bridge = dev.getBridge(self)
		if self.isConnected():
			if not ifaceutil.bridgeExists(dev.host, bridge):
				ifaceutil.bridgeCreate(dev.host, bridge)
			ifaceutil.bridgeConnect(dev.host, bridge, self.interfaceName())
			ifaceutil.ifup(dev.host, self.interfaceName())
			
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
			
	def getStartTasks(self):
		taskset = Interface.getStartTasks(self)
		connect_to_bridge = tasks.Task("connect-to-bridge", self.connectToBridge)
		taskset.add(connect_to_bridge)
		taskset.add(tasks.Task("configure-network", self._configureNetwork, after=connect_to_bridge))
		return taskset

	def getPrepareTasks(self):
		return Interface.getPrepareTasks(self)

	def toDict(self, auth):
		res = Interface.toDict(self, auth)
		res["attrs"].update(ip4address=self.getAttribute("ip4address"), ip6address=self.getAttribute("ip6address"),
			use_dhcp=self.getAttribute("use_dhcp"))	
		return res				