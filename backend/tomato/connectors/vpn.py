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
import hashlib

import emulated

from tomato import fault, hosts, config
from tomato.hosts import resources
from tomato.generic import State
from tomato.connectors import Connector
from tomato.lib import util, tinc, tasks, ifaceutil, vtun
from tomato.topology import Permission 

class ConnectionEndpoint(tinc.Endpoint):
	def __init__(self, con):
		self.con = con
	def getSite(self):
		return self.getHost().group
	def hasHost(self):
		return self.con.upcast().getTincHost()
	def getHost(self):
		host = self.con.upcast().getTincHost()
		assert host
		return host
	def getId(self):
		return self.con.id
	def getPort(self):
		port = self.con.upcast().getTincPort()
		assert port
		return port
	def getBridge(self):
		bridge = self.con.upcast().getBridge()
		assert bridge
		return bridge
	def getSubnets(self):
		subnets = []
		if self.con.connector.type == tinc.Mode.ROUTER:
			subnets.append(util.calculate_subnet4(self.con.getAttribute("gateway4")))
			subnets.append(util.calculate_subnet6(self.con.getAttribute("gateway6")))
		return subnets
	def getGateways(self):
		gws = []
		if self.con.connector.type == tinc.Mode.ROUTER:
			gws.append(self.con.getAttribute("gateway4"))
			gws.append(self.con.getAttribute("gateway6"))
		return gws
	def __repr__(self):
		return str(self.con)


class TincConnector(Connector):

	external_access_port = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	EXTERNAL_ACCESS_PORT_SLOT = "ea"

	class Meta:
		db_table = "tomato_tincconnector"
		app_label = 'tomato'

	def upcast(self):
		return self

	def _endpoints(self):
		endpoints = set()
		for con in self.connectionSetAll():
			endpoints.add(ConnectionEndpoint(con))
		return endpoints
	
	def getExternalAccessPort(self):
		res = resources.get(self, self.EXTERNAL_ACCESS_PORT_SLOT, "external_access_port")
		if res:
			return res.num

	def getExternalAccessHost(self):
		res = resources.get(self, self.EXTERNAL_ACCESS_PORT_SLOT, "external_access_port")
		if res:
			return res.getHost()
	
	def getExternalAccess(self):
		return self.getAttribute("external_access", False)
	
	def setExternalAccess(self, flag):
		self.setAttribute("external_access", flag)
		
	def getExternalAccessPassword(self):
		if not self.getExternalAccess():
			return False
		m = hashlib.md5()
		m.update(config.PASSWORD_SALT)
		m.update(str(self.name))
		m.update(str(self.getExternalAccessPort()))
		m.update(str(self.topology.owner))
		return m.hexdigest()
			
	def getCapabilities(self, user):
		capabilities = Connector.getCapabilities(self, user)
		capabilities["configure"].update({
			"external_access": self.state == State.CREATED,
		})
		capabilities["action"].update({
			"download_capture": self.state != State.CREATED,
		})
		capabilities.update(other={
			"external_access": self.state == State.STARTED and self.getExternalAccess()
		})
		return capabilities

	def _runAction(self, action, attrs, direct):
		if action == "download_capture":
			interface = self.topology.interfacesGet(attrs["iface"])
			fault.check(interface, "No such interface: %s", attrs["iface"])
			con = interface.connection.upcast()
			assert con.connector.id == self.id
			return con.downloadCaptureUri()
		else:
			return Connector._runAction(self, action, attrs, direct)			
				
	def _startExternalAccess(self):
		if not self.getExternalAccess():
			return
		assert self.getExternalAccessPort()
		vtun.start(self.getExternalAccessHost(), self.getExternalAccessPort())
				
	def getStartTasks(self):
		taskset = Connector.getStartTasks(self)
		tinc_tasks = tinc.getStartNetworkTasks(self._endpoints(), self.type)
		taskset.add(tinc_tasks)
		tinc_tasks_dummy = tasks.Task("tinc_started")
		tinc_tasks_dummy.after(tinc_tasks)
		taskset.add(tinc_tasks_dummy)
		for con in self.connectionSetAll():
			ts = con.upcast().getStartTasks()
			ts.prefix(con).after(tinc_tasks_dummy)
			taskset.add(ts)
		taskset.add(tasks.Task("start-external-access", self._startExternalAccess))
		return self._adaptTaskset(taskset)

	def _stopExternalAccess(self):
		if not self.getExternalAccess():
			return
		if not self.getExternalAccessPort():
			return
		vtun.stop(self.getExternalAccessHost(), self.getExternalAccessPort())

	def getStopTasks(self):
		taskset = Connector.getStopTasks(self)
		taskset.add(tinc.getStopNetworkTasks(self._endpoints(), self.type))
		for con in self.connectionSetAll():
			taskset.add(con.upcast().getStopTasks().prefix(con))
		taskset.add(tasks.Task("stop-external-access", self._stopExternalAccess))
		return self._adaptTaskset(taskset)
		
	def _assignResources(self):
		for con in self.connectionSetAll():
			con.upcast().prepareBridge()
			con.upcast()._assignTincPort()
		
	def _prepareExternalAccess(self):
		if not self.getExternalAccess():
			return
		self._assignVtunData()
		host = self.getExternalAccessHost()
		port = self.getExternalAccessPort()
		assert port
		password = self.getExternalAccessPassword()
		assert password
		for con in self.connectionSetAll():
			if con.getHost() == host:
				bridge = con.upcast().getBridge()
		assert bridge
		vtun.prepare(host, port, password, bridge)

	def getPrepareTasks(self):
		taskset = Connector.getPrepareTasks(self)
		assign_resources = tasks.Task("assign-resources", self._assignResources)
		tinc_tasks = tinc.getPrepareNetworkTasks(self._endpoints(), self.type)
		tinc_tasks.after(assign_resources)
		taskset.add([assign_resources, tinc_tasks])
		taskset.add(tasks.Task("prepare-external-access", self._prepareExternalAccess))
		return self._adaptTaskset(taskset)

	def _unassignResources(self):
		for con in self.connectionSetAll():
			con.upcast()._unassignTincPort()
			con.upcast().destroyBridge()

	def _destroyExternalAccess(self):
		if not self.getExternalAccess():
			return
		if not self.getExternalAccessPort():
			return
		vtun.destroy(self.getExternalAccessHost(), self.getExternalAccessPort())
		self._unassignVtunData()

	def getDestroyTasks(self):
		taskset = Connector.getDestroyTasks(self)
		tinc_tasks = tinc.getDestroyNetworkTasks(self._endpoints(), self.type)
		unassign_resources = tasks.Task("destroy-bridges", self._unassignResources, after=tinc_tasks)
		taskset.add([tinc_tasks, unassign_resources])
		taskset.add(tasks.Task("destroy-external-access", self._destroyExternalAccess))
		return self._adaptTaskset(taskset)

	def configure(self, properties):
		Connector.configure(self, properties)
		if "external_access" in properties:
			self.setExternalAccess(properties["external_access"])
	
	def connectionsAdd(self, iface_name, properties):
		iface = self.topology.interfacesGet(iface_name)
		fault.check(self.state == State.CREATED, "Cannot add connections to started or prepared connector: %s -> %s", (iface_name, self.name) )
		fault.check(iface.device.state != State.STARTED, "Cannot add connections to running device: %s -> %s", (iface_name, self.name) )
		fault.check(not iface.isConnected(), "Cannot add connections to connected interface: %s -> %s", (iface_name, self.name) )
		con = TincConnection()
		con.connector = self
		con.interface = iface
		con.init()
		con.configure(properties)
		con.save()

	def connectionsConfigure(self, iface_name, properties):
		iface = self.topology.interfacesGet(iface_name)
		con = self.connectionSetGet(iface)
		con.configure(properties)
		con.save()	
	
	def connectionsDelete(self, iface_name): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfacesGet(iface_name)
		fault.check(self.state == State.CREATED, "Cannot delete connections from started or prepared connector: %s -> %s", (iface_name, self.name) )
		fault.check(iface.device.state != State.STARTED, "Cannot delete connections from running device: %s -> %s", (iface_name, self.name) )
		con = self.connectionSetGet(iface)
		con.delete()

	def getResourceUsage(self):
		disk = tinc.estimateDiskUsage(len(self.connectionSetAll())) if self.state != State.CREATED else 0
		memory = tinc.estimateMemoryUsage(len(self.connectionSetAll())) if self.state == State.STARTED else 0
		ports = len(self.connectionSetAll()) if self.state == State.STARTED else 0
		if self.getExternalAccessPort():
			ports += 1 if self.state == State.STARTED else 0
			disk += 500 if self.state != State.CREATED else 0
			memory += 200000 if self.state == State.STARTED else 0
		traffic = 0
		for con in self.connectionSetAll():
			dev = con.interface.device
			if dev.host and dev.state == State.STARTED:
				iface = dev.upcast().interfaceDevice(con.interface)
				try:
					traffic += ifaceutil.getRxBytes(dev.host, iface) + ifaceutil.getTxBytes(dev.host, iface)
				except:
					pass
		return {"disk": disk, "memory": memory, "ports": ports, "traffic": traffic}		

	def getBridge(self, connection, create=True):
		bridge_id = connection.upcast().getBridgeId()
		assert bridge_id
		name = "gbr_%d" % bridge_id
		if create:
			host = connection.getHost()
			ifaceutil.bridgeCreate(host, name)
		return name

	def _assignVtunData(self):
		host = None
		for con in self.connectionSetAll():
			if con.interface.device.host:
				host = con.interface.device.host
				break
		fault.check(host, "Failed to assign a host for external access")		
		if not self.getExternalAccessPort():
			self.external_access_port = resources.take(host, "port", self, self.EXTERNAL_ACCESS_PORT_SLOT)
			self.save()

	def _unassignVtunData(self):
		if self.getExternalAccessPort():
			self.external_access_port = None
			self.save()
			resources.give(self, self.EXTERNAL_ACCESS_PORT_SLOT)

	def toDict(self, auth):
		res = Connector.toDict(self, auth)
		res["attrs"].update(external_access=self.getExternalAccess())
		if auth:
			if self.getExternalAccess():
				if self.getExternalAccessPort():
					res["attrs"]["external_access_host"] = self.getExternalAccessHost().name
					res["attrs"]["external_access_port"] = self.getExternalAccessPort()
					res["attrs"]["external_access_password"] = self.getExternalAccessPassword()
		return res


class TincConnection(emulated.EmulatedConnection):

	tinc_port = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	TINC_PORT_SLOT = "tinc"
	bridge_id = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	BRIDGE_ID_SLOT = "b"

	class Meta:
		db_table = "tomato_tincconnection"
		app_label = 'tomato'

	def upcast(self):
		return self
	
	def getTincPort(self):
		res = resources.get(self, self.TINC_PORT_SLOT, "tinc_port")
		if res:
			return res.num
	
	def getTincHost(self):
		res = resources.get(self, self.TINC_PORT_SLOT, "tinc_port")
		if res:
			return res.getHost()

	def getBridgeId(self):
		res = resources.get(self, self.BRIDGE_ID_SLOT, "bridge_id")
		if res:
			return res.num
	
	def getBridgeHost(self):
		res = resources.get(self, self.BRIDGE_ID_SLOT, "bridge_id")
		if res:
			return res.getHost()
	
	def getCapabilities(self, user):
		capabilities = emulated.EmulatedConnection.getCapabilities(self, user)
		con = self.connector
		capabilities["configure"].update({
			"gateway4": con.state == State.CREATED and con.type == "router",
			"gateway6": con.state == State.CREATED and con.type == "router",
		})
		return capabilities
	
	def configure(self, properties):
		if "gateway4" in properties or "gateway6" in properties:
			fault.check(self.connector.state == State.CREATED, "Cannot change gateways on prepared or started router: %s" % self)
		emulated.EmulatedConnection.configure(self, properties)
		if self.connector.type == "router":
			for key in ["gateway4", "gateway6"]:
				if key in properties:
					self.setAttribute(key, properties[key])
			if not self.hasAttribute("gateway4"):
				self.setAttribute("gateway4", "10.0.0.254/24") 
			if not self.hasAttribute("gateway6"):
				self.setAttribute("gateway6", "fd01:ab1a:b1ab:0:0:FFFF:FFFF:FFFF/80") 
			if not len(self.getAttribute("gateway4").split("/")) == 2:
				self.setAttribute("gateway4", self.getAttribute("gateway4") + "/24")
			if not len(self.getAttribute("gateway6").split("/")) == 2:
				self.setAttribute("gateway6", self.getAttribute("gateway6") + "/80")
		
	def _assignTincPort(self):
		if not self.getTincPort():
			host = self.getHost()
			assert host
			self.tinc_port = resources.take(host, "port", self, self.TINC_PORT_SLOT)
			self.save()

	def prepareBridge(self):
		self._assignBridgeId()

	def destroyBridge(self):
		if self.connector.state == State.STARTED:
			return
		if not self.getBridgeId():
			return
		if self.interface.device.state != State.CREATED and ifaceutil.bridgeInterfaces(self.getBridgeHost(), self.getBridge()):
			return
		ifaceutil.bridgeRemove(self.getBridgeHost(), self.getBridge(), disconnectAll=True, setIfdown=True)
		self._unassignBridgeId()

	def _assignBridgeId(self):
		if not self.getBridgeId():
			host = self.getHost()
			assert host
			self.bridge_id = resources.take(host, "bridge", self, self.BRIDGE_ID_SLOT)
			self.save()

	def _unassignBridgeId(self):
		if self.getBridgeId():
			self.bridge_id = None
			self.save()
			resources.give(self, self.BRIDGE_ID_SLOT)
			
	def _unassignTincPort(self):
		if self.getTincPort():
			self.tinc_port = None
			self.save()
			resources.give(self, self.TINC_PORT_SLOT)

	def getDestroyTasks(self):
		taskset = emulated.EmulatedConnection.getDestroyTasks(self)
		taskset.add(tasks.Task("destroy-bridge", self.destroyBridge))
		return taskset

	def internalInterface(self):
		return tinc.interfaceName(ConnectionEndpoint(self))

	def toDict(self, auth):
		res = emulated.EmulatedConnection.toDict(self, auth)
		res["attrs"].update(gateway4=self.getAttribute("gateway4"), gateway6=self.getAttribute("gateway6"))	
		return res
