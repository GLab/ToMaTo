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

import dummynet

from tomato import fault
from tomato.generic import State
from tomato.connectors import Connector
from tomato.lib import util, tinc, tasks, ifaceutil
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
			
	def getCapabilities(self, user):
		capabilities = Connector.getCapabilities(self, user)
		capabilities["action"].update({
			"download_capture": self.state != State.CREATED,
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
				
	def getStartTasks(self):
		taskset = Connector.getStartTasks(self)
		tinc_tasks = tinc.getStartNetworkTasks(self._endpoints(), self.type)
		taskset.add(tinc_tasks)		
		for con in self.connectionSetAll():
			ts = con.upcast().getStartTasks()
			ts.prefix(con).after(tinc_tasks)
			taskset.add(ts)
		return self._adaptTaskset(taskset)

	def getStopTasks(self):
		taskset = Connector.getStopTasks(self)
		taskset.add(tinc.getStopNetworkTasks(self._endpoints(), self.type))
		for con in self.connectionSetAll():
			taskset.add(con.upcast().getStopTasks().prefix(con))
		return self._adaptTaskset(taskset)
		
	def _assignResources(self):
		for con in self.connectionSetAll():
			con.upcast()._assignTincPort()
		
	def getPrepareTasks(self):
		taskset = Connector.getPrepareTasks(self)
		assign_resources = tasks.Task("assign-resources", self._assignResources)
		tinc_tasks = tinc.getPrepareNetworkTasks(self._endpoints(), self.type)
		tinc_tasks.after(assign_resources)
		taskset.add([assign_resources, tinc_tasks])
		return self._adaptTaskset(taskset)

	def _unassignResources(self):
		for con in self.connectionSetAll():
			con.upcast()._unassignTincPort()
			host = con.interface.device.host
			if con.bridge_id and not ifaceutil.bridgeInterfaces(host, con.getBridge()):
				con.upcast()._unassignBridgeId()

	def getDestroyTasks(self):
		taskset = Connector.getDestroyTasks(self)
		tinc_tasks = tinc.getDestroyNetworkTasks(self._endpoints(), self.type)
		unassign_resources = tasks.Task("unassign-resources", self._unassignResources, after=tinc_tasks)
		taskset.add([tinc_tasks, unassign_resources])
		return self._adaptTaskset(taskset)

	def configure(self, properties):
		Connector.configure(self, properties)
	
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

	def getResourceUsage(self):
		disk = tinc.estimateDiskUsage(len(self.connectionSetAll())) if self.state != State.CREATED else 0
		memory = tinc.estimateMemoryUsage(len(self.connectionSetAll())) if self.state == State.STARTED else 0
		ports = len(self.connectionSetAll()) if self.state == State.STARTED else 0		
		return {"disk": disk, "memory": memory, "ports": ports}		


class TincConnection(dummynet.EmulatedConnection):

	tinc_port = models.PositiveIntegerField(null=True)

	class Meta:
		db_table = "tomato_tincconnection"
		app_label = 'tomato'

	def upcast(self):
		return self
	
	def getIdUsage(self, host):
		ids = dummynet.EmulatedConnection.getIdUsage(self, host)
		if self.tinc_port and self.interface.device.host == host:
			ids["port"] = ids.get("port", set()) | set((self.tinc_port,))
		return ids

	def getCapabilities(self, user):
		capabilities = dummynet.EmulatedConnection.getCapabilities(self, user)
		con = self.connector
		capabilities["configure"].update({
			"gateway4": con.state == State.CREATED and con.type == "router",
			"gateway6": con.state == State.CREATED and con.type == "router",
		})
		return capabilities
	
	def configure(self, properties):
		if "gateway4" in properties or "gateway6" in properties:
			fault.check(self.connector.state == State.CREATED, "Cannot change gateways on prepared or started router: %s" % self)
		dummynet.EmulatedConnection.configure(self, properties)
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
			if self.connector.state != State.STARTED and self.interface.device.state != State.STARTED:
				host = self.getHost()
				if host:
					bridge = self.getBridge(assign=False, create=False)
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

	def onInterfaceStateChange(self):
		dummynet.EmulatedConnection.onInterfaceStateChange(self)
		self._unassignBridgeId()

	def toDict(self, auth):
		res = dummynet.EmulatedConnection.toDict(self, auth)
		res["attrs"].update(gateway4=self.getAttribute("gateway4"), gateway6=self.getAttribute("gateway6"))	
		if auth:
			res["attrs"]["tinc_port"] = self.tinc_port	
		return res
