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

import dummynet

from tomato import fault
from tomato.generic import State
from tomato.connectors import Connector
from tomato.lib import util, tinc, tasks

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
		port = self.con.attributes["tinc_port"]
		assert port
		return port
	def getBridge(self):
		bridge = self.con.upcast().bridgeName()
		assert bridge
		return bridge
	def getSubnets(self):
		subnets = []
		if self.con.connector.type == tinc.Mode.ROUTER:
			subnets.append(util.calculate_subnet4(self.con.attributes["gateway4"]))
			subnets.append(util.calculate_subnet6(self.con.attributes["gateway6"]))
		return subnets


class TincConnector(Connector):

	class Meta:
		db_table = "tomato_tincconnector"

	def upcast(self):
		return self

	def _endpoints(self):
		endpoints = set()
		for con in self.connectionSetAll():
			endpoints.add(ConnectionEndpoint(con))
		return endpoints
		
	def getStartTasks(self):
		taskset = Connector.getStartTasks(self)
		taskset.addTaskSet("tinc-start", tinc.getStartNetworkTasks(self._endpoints(), self.type))
		return taskset

	def getStopTasks(self):
		taskset = Connector.getStopTasks(self)
		taskset.addTaskSet("tinc-stop", tinc.getStopNetworkTasks(self._endpoints(), self.type))
		return taskset
		
	def _assignResources(self):
		for con in self.connectionSetAll():
			con.upcast()._assignTincPort()
			con.upcast()._assignBridgeId()
		
	def getPrepareTasks(self):
		taskset = Connector.getPrepareTasks(self)
		taskset.addTask(tasks.Task("assign-resources", self._assignResources))
		taskset.addTaskSet("tinc-prepare", tinc.getPrepareNetworkTasks(self._endpoints(), self.type).addGlobalDepends("assign-resources"))
		return taskset

	def _unassignResources(self):
		for con in self.connectionSetAll():
			con.upcast()._unassignTincPort()
			con.upcast()._unassignBridgeId()

	def getDestroyTasks(self):
		taskset = Connector.getDestroyTasks(self)
		ts = tinc.getDestroyNetworkTasks(self._endpoints(), self.type)
		last = ts.getLastTask()
		taskset.addTaskSet("tinc-destroy", ts)
		taskset.addLastTask(tasks.Task("unassign-resources", self._unassignResources, depends=last.name))
		return taskset

	def configure(self, properties):
		Connector.configure(self, properties)
	
	def connectionsAdd(self, iface_name, properties):
		iface = self.topology.interfacesGet(iface_name)
		if self.state == State.STARTED or self.state == State.PREPARED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to started or prepared connector: %s -> %s" % (iface_name, self.name) )
		if iface.device.state == State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to running device: %s -> %s" % (iface_name, self.name) )
		if iface.isConnected():
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to connected interface: %s -> %s" % (iface_name, self.name) )
		con = TincConnection ()
		con.init()
		con.connector = self
		con.interface = iface
		con.configure(properties)
		con.save()

	def connectionsConfigure(self, iface_name, properties):
		iface = self.topology.interfacesGet(iface_name)
		con = self.connectionSetGet(iface)
		con.configure(properties)
		con.save()	
	
	def connectionsDelete(self, iface_name): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfacesGet(iface_name)
		if self.state == State.STARTED or self.state == State.PREPARED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to started or prepared connector: %s -> %s" % (iface_name, self.name) )
		if iface.device.state == State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to running devices: %s -> %s" % (iface_name, self.name) )
		con = self.connectionSetGet(iface)
		con.delete()

	def getResourceUsage(self):
		disk = tinc.estimateDiskUsage(len(self.connectionSetAll())) if self.state != State.CREATED else 0
		memory = tinc.estimateMemoryUsage(len(self.connectionSetAll())) if self.state == State.STARTED else 0
		ports = len(self.connectionSetAll()) if self.state == State.STARTED else 0		
		return {"disk": disk, "memory": memory, "ports": ports}		


class TincConnection(dummynet.EmulatedConnection):

	class Meta:
		db_table = "tomato_tincconnection"

	def upcast(self):
		return self
	
	def configure(self, properties):
		if "gateway4" in properties or "gateway6" in properties:
			assert self.connector.state == State.CREATED, "Cannot change gateways on prepared or started router: %s" % self
		dummynet.EmulatedConnection.configure(self, properties)
		if self.connector.type == "router":
			if not self.attributes["gateway4"]:
				self.attributes["gateway4"] = "10.0.0.254/24" 
			if not self.attributes["gateway6"]:
				self.attributes["gateway6"] = "fd01:ab1a:b1ab:0:0:FFFF:FFFF:FFFF/80" 
			if not len(self.attributes["gateway4"].split("/")) == 2:
				self.attributes["gateway4"] = self.attributes["gateway4"] + "/24"
			if not len(self.attributes["gateway6"].split("/")) == 2:
				self.attributes["gateway6"] = self.attributes["gateway6"] + "/80"
		
	def _assignBridgeId(self):
		if not self.attributes["bridge_id"]:
			self.attributes["bridge_id"] = self.interface.device.host.nextFreeBridge()		
			self.save()

	def _assignTincPort(self):
		if not self.attributes["tinc_port"]:
			self.attributes["tinc_port"] = self.interface.device.host.nextFreePort()
			self.save()

	def _unassignBridgeId(self):
		del self.attributes["bridge_id"]

	def _unassignTincPort(self):
		del self.attributes["tinc_port"]

	def toDict(self, auth):
		res = dummynet.EmulatedConnection.toDict(self, auth)	
		if not auth:
			del res["attrs"]["tinc_port"]	
			del res["attrs"]["bridge_id"]	
		return res
