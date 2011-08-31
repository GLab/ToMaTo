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
from tomato.generic import State
from tomato.connectors import Connector
from tomato.lib import util, tinc, tasks, ifaceutil, vtun
from tomato.topology import Permission 

class ConnectionEndpoint(tinc.Endpoint):
	def __init__(self, con):
		self.con = con
	def getSite(self):
		return self.getHost().group
	def getHost(self):
		host = self.con.interface.device.host
		assert host
		return host
	def getId(self):
		return self.con.id
	def getPort(self):
		port = self.con.upcast().tinc_port
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
	
	def getExternalAccess(self):
		return self.getAttribute("external_access", False)
	
	def setExternalAccess(self, flag):
		self.setAttribute("external_access", flag)
		
	def getExternalAccessPort(self):
		return self.getAttribute("external_access_port")
	
	def setExternalAccessPort(self, port):
		self.setAttribute("external_access_port", port)
	
	def getExternalAccessCon(self):
		cname = self.getAttribute("external_access_con")
		if cname:
			return self.topology.interfacesGet(cname).connection
	
	def setExternalAccessCon(self, con):
		if con:
			self.setAttribute("external_access_con", str(con.interface))
		else:
			self.deleteAttribute("external_access_con")
		
	def getExternalAccessHost(self):
		con = self.getExternalAccessCon()
		if con:
			return con.interface.device.host

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
		host = self.getExternalAccessHost()
		assert host
		port = self.getExternalAccessPort()
		assert port
		vtun.start(host, port)
				
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
		host = self.getExternalAccessHost()
		assert host
		port = self.getExternalAccessPort()
		assert port
		vtun.stop(host, port)

	def getStopTasks(self):
		taskset = Connector.getStopTasks(self)
		taskset.add(tinc.getStopNetworkTasks(self._endpoints(), self.type))
		for con in self.connectionSetAll():
			taskset.add(con.upcast().getStopTasks().prefix(con))
		taskset.add(tasks.Task("stop-external-access", self._stopExternalAccess))
		return self._adaptTaskset(taskset)
		
	def _assignResources(self):
		for con in self.connectionSetAll():
			con.upcast()._assignTincPort()
		
	def _prepareExternalAccess(self):
		if not self.getExternalAccess():
			return
		self._assignVtunData()
		host = self.getExternalAccessHost()
		assert host
		port = self.getExternalAccessPort()
		assert port
		password = self.getExternalAccessPassword()
		assert password
		bridge = self.getExternalAccessCon().getBridge()
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
			host = con.interface.device.host
			if con.bridge_id and not ifaceutil.bridgeInterfaces(host, con.getBridge()):
				con.upcast()._unassignBridgeId()

	def _destroyExternalAccess(self):
		if not self.getExternalAccess():
			return
		host = self.getExternalAccessHost()
		if not host:
			return
		port = self.getExternalAccessPort()
		if port:
			vtun.destroy(host, port)
		self._unassignVtunData()

	def getDestroyTasks(self):
		taskset = Connector.getDestroyTasks(self)
		tinc_tasks = tinc.getDestroyNetworkTasks(self._endpoints(), self.type)
		unassign_resources = tasks.Task("unassign-resources", self._unassignResources, after=tinc_tasks)
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
		con = TincConnection ()
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

	def getIdUsage(self, host):
		ids = Connector.getIdUsage(self, host)
		if self.getExternalAccess() and self.state != State.CREATED:
			if self.getAttribute("external_access_host") == host.name:
				ids["port"] = ids.get("port", set()) | set((self.getAttribute("external_access_port"),))
		return ids

	def getResourceUsage(self):
		disk = tinc.estimateDiskUsage(len(self.connectionSetAll())) if self.state != State.CREATED else 0
		memory = tinc.estimateMemoryUsage(len(self.connectionSetAll())) if self.state == State.STARTED else 0
		ports = len(self.connectionSetAll()) if self.state == State.STARTED else 0
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

	def _assignVtunData(self):
		host = None
		if self.getExternalAccessCon():
			host = self.getExternalAccessHost()
		if not host:
			for con in self.connectionSetAll():
				if con.interface.device.host:
					self.setExternalAccessCon(con)
					host = con.interface.device.host
					self.setExternalAccessPort(None)
					break
		fault.check(host, "Failed to assign a host for external access")		
		if not self.getExternalAccessPort():
			host.takeId("port", self.setExternalAccessPort)

	def _unassignVtunData(self):
		if self.getExternalAccessHost():
			host = self.getExternalAccessHost()
			if self.getExternalAccessPort():
				host.giveId("port", self.getExternalAccessPort())
				self.setExternalAccessPort(None)
			self.setExternalAccessCon(None)

	def toDict(self, auth):
		res = Connector.toDict(self, auth)
		res["attrs"].update(external_access=self.getExternalAccess())
		if auth:
			if self.getExternalAccess():
				if self.getExternalAccessHost():
					res["attrs"]["external_access_host"] = self.getExternalAccessHost().name
				if self.getExternalAccessPort():
					res["attrs"]["external_access_port"] = self.getExternalAccessPort()
					res["attrs"]["external_access_password"] = self.getExternalAccessPassword()
		return res


class TincConnection(emulated.EmulatedConnection):

	tinc_port = models.PositiveIntegerField(null=True)

	class Meta:
		db_table = "tomato_tincconnection"
		app_label = 'tomato'

	def upcast(self):
		return self
	
	def getIdUsage(self, host):
		ids = emulated.EmulatedConnection.getIdUsage(self, host)
		if self.tinc_port and self.interface.device.host == host:
			ids["port"] = ids.get("port", set()) | set((self.tinc_port,))
		return ids

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
	
	def _setTincPort(self, port):
		self.tinc_port = port
		self.save()
			
	def _assignTincPort(self):
		if not self.tinc_port:
			host = self.getHost()
			assert host
			host.takeId("port", self._setTincPort)

	def _unassignBridgeId(self):
		if self.bridge_id:
			host = self.getHost()
			if host:
				bridge = self.getBridge(create=False)
				if ifaceutil.bridgeExists(host, bridge):
					attachedInterfaces = ifaceutil.bridgeInterfaces(host, bridge)
					assert not attachedInterfaces, "Bridge %s still has interfaces connected: %s" % (bridge, attachedInterfaces) 
					ifaceutil.bridgeRemove(host, bridge)			
				host.giveId("bridge", self.bridge_id)
			self.bridge_id = None
			self.save()

	def _unassignTincPort(self):
		if self.tinc_port:
			host = self.getHost()
			assert host
			host.giveId("port", self.tinc_port)
		self.tinc_port = None
		self.save()

	def internalInterface(self):
		return tinc.interfaceName(ConnectionEndpoint(self))

	def toDict(self, auth):
		res = emulated.EmulatedConnection.toDict(self, auth)
		res["attrs"].update(gateway4=self.getAttribute("gateway4"), gateway6=self.getAttribute("gateway6"))	
		if auth:
			res["attrs"]["tinc_port"] = self.tinc_port	
		return res
