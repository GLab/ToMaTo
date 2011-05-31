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
		self.setTemplate("")
		self.setRootPassword("glabroot")

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
				bridge = self.bridgeName(iface)
				assert bridge, "Interface has no bridge %s" % iface
				ifaceutil.bridgeCreate(self.host, bridge)
				ifaceutil.ifup(self.host, bridge)

	def _configureRoutes(self):
		#Note: usage of self as host is intentional
		if self.hasAttribute("gateway4"):
			ifaceutil.setDefaultRoute(self, self.getAttribute("gateway4")) 
		if self.hasAttribute("gateway6"):
			ifaceutil.setDefaultRoute(self, self.getAttribute("gateway6")) 

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
		for iface in self.interfaceSetAll():
			ts = iface.upcast().getStartTasks()
			ts.prefix(iface).after(check_interfaces_exist)
			taskset.add(ts)
		configure_routes = tasks.Task("configure-routes", self._configureRoutes, reverseFn=self._fallbackStop, after=start_vm)
		assign_vnc_port = tasks.Task("assign-vnc-port", self._assignVncPort, reverseFn=self._fallbackStop)
		start_vnc = tasks.Task("start-vnc", self._startVnc, reverseFn=self._fallbackStop, after=[start_vm, assign_vnc_port])
		taskset.add([create_bridges, start_vm, check_interfaces_exist, configure_routes, assign_vnc_port, start_vnc])
		return taskset

	def _stopVnc(self):
		assert self.host and self.getVmid() and self.getVncPort()
		vzctl.stopVnc(self.host, self.getVmid(), self.getVncPort())
		self.setVncPort(None)
	
	def _stopVm(self):
		vzctl.stop(self.host, self.getVmid())

	def getStopTasks(self):
		taskset = Device.getStopTasks(self)
		stop_vnc = tasks.Task("stop-vnc", self._stopVnc, reverseFn=self._fallbackStop)
		stop_vm = tasks.Task("stop-vm", self._stopVm, reverseFn=self._fallbackStop)
		unassign_vnc_port = tasks.Task("unassign-vnc-port", self._unassignVncPort, reverseFn=self._fallbackStop, after=stop_vnc)
		taskset.add([stop_vnc, stop_vm, unassign_vnc_port])
		return taskset	

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
		return taskset

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
			if self.getAttribute("gateway4") and self.state == State.STARTED:
				#Note: usage of self as host is intentional
				ifaceutil.setDefaultRoute(self, self.getAttribute("gateway4"))
		if "gateway6" in properties:
			self.setAttribute("gateway4", properties["gateway4"])
			if self.getAttribute("gateway6") and self.state == State.STARTED:
				#Note: usage of self as host is intentional
				ifaceutil.setDefaultRoute(self, self.getAttribute("gateway6"))
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
		iface.init()
		iface.name = name
		iface.device = self
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
		if self.state == State.PREPARED or self.state == State.STARTED:
			iface.prepare_run()
		if self.state == State.STARTED:
			iface.start_run()	
		iface.save()

	def interfacesDelete(self, name):
		iface = self.interfaceSetGet(name).upcast()
		if self.state == State.PREPARED or self.state == State.STARTED:
			vzctl.deleteInterface(self.host, self.getVmid(), iface.name)
		iface.delete()

	def migrateRun(self, host=None):
		#FIXME: both vmids must be reserved the whole time
		if self.state == State.CREATED:
			self._unassignHost()
			self._unassignVmid()
			return
		#save src data
		src_host = self.host
		src_vmid = self.getVmid()
		#assign new host and vmid
		self._unassignHost()
		self._unassignVmid()
		if host:
			self.host = host
		else:
			self._assignHost()
		self._assignVmid()
		dst_host = self.host
		dst_vmid = self.getVmid()
		#reassign host and vmid
		self.host = src_host
		self.setVmid(src_vmid)
		#destroy all connectors and save their state
		constates={}
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector
				if con.name in constates:
					continue
				constates[con.name] = con.state
				if con.state == State.STARTED:
					con.stop(True)
				if con.state == State.PREPARED:
					con.destroy(True)
		#actually migrate the vm
		if self.state == State.STARTED:
			self._stopVnc()
		vzctl.migrate(src_host, src_vmid, dst_host, dst_vmid)
		if self.state == State.STARTED:
			self._startVnc()
		#switch host and vmid
		self.host = dst_host
		self.setVmid(dst_vmid)
		#redeploy all connectors
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector
				if not con.name in constates:
					continue
				state = constates[con.name]
				del constates[con.name]
				if state == State.PREPARED or state == State.STARTED:
					con.prepare(True)
				if state == State.STARTED:
					con.start(True)
		
	def uploadSupported(self):
		return self.state == State.PREPARED

	def useUploadedImageRun(self, path):
		assert self.uploadSupported(), "Upload not supported"
		vzctl.useImage(self.host, self.getVmid(), path, forceGzip=True)
		self.setTemplate("***custom***")

	def downloadSupported(self):
		return self.state == State.PREPARED

	def downloadImageUri(self):
		assert self.downloadSupported(), "Download not supported"
		filename = "%s_%s.tar.gz" % (self.topology.name, self.name)
		file = hostserver.randomFilename(self.host)
		vzctl.copyImage(self.host, self.getVmid(), file)
		return hostserver.downloadGrant(self.host, file, filename)

	def getResourceUsage(self):
		disk = 0
		memory = 0
		ports = 1 if self.state == State.STARTED else 0		
		if self.host and self.getVmid():
			disk = vzctl.getDiskUsage(self.host, self.getVmid())
			memory = vzctl.getMemoryUsage(self.host, self.getVmid())
		return {"disk": disk, "memory": memory, "ports": ports}		

	def getIdUsage(self):
		ids = Device.getIdUsage(self)
		if self.vnc_port:
			ids["port"] = ids.get("port", set()) | set((self.vnc_port,))
		if self.vmid:
			ids["vmid"] = ids.get("vmid", set()) | set((self.vmid,))
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
		self.setAttribute("use_dhcp", False)
	
	def upcast(self):
		return self

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

	def _connectToBridge(self):
		dev = self.device.upcast()
		bridge = dev.bridgeName(self)
		if self.isConnected():
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
		connect_to_bridge = tasks.Task("connect-to-bridge", self._connectToBridge)
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