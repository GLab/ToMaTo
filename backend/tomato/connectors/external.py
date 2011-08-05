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
from tomato import fault, hosts

from tomato.connectors import Connector, Connection
from tomato.generic import State, ObjectPreferences
from tomato.lib import ifaceutil, tasks
from tomato.topology import Permission

class ExternalNetworkConnector(Connector):
	used_network = models.ForeignKey(hosts.ExternalNetwork, null=True) 
	network_type = models.CharField(max_length=20, default="internet")
	network_group = models.CharField(max_length=20, null=True)
	
	class Meta:
		db_table = "tomato_externalnetworkconnector"
		app_label = 'tomato'

	def init(self):
		self.attrs = {}

	def upcast(self):
		return self

	def getNetworkType(self):
		return self.network_type
	
	def setNetworkType(self, value):
		self.network_type = value

	def getNetworkGroup(self):
		return self.network_group
	
	def setNetworkGroup(self, value):
		self.network_group = value

	def _updateHostPreferences(self, prefs, en):
		if not en.hasFreeSlots():
			return
		hosts = []
		used = en.usageCount()
		if en.avoid_duplicates:
			for con in self.connectionSetAll():
				dev = con.interface.device
				if dev.host:
					hosts.append(dev.host)
		for enb in en.externalnetworkbridge_set.all():
			if enb.host.enabled and not (en.avoid_duplicates and (enb.host in hosts)):
				if en.max_devices:
					prefs.add(enb.host, 1.0-used/en.max_devices)
				else:
					prefs.add(enb.host, 1.0)
		
	def hostPreferences(self):
		prefs = ObjectPreferences(True)
		if self.used_network:
			self._updateHostPreferences(prefs, self.used_network)
		else:
			for en in self.networkOptions().objects:
				self._updateHostPreferences(prefs, en)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def networkOptions(self):
		options = ObjectPreferences(True)
		ens = hosts.ExternalNetwork.objects.filter(type=self.getNetworkType())
		if self.getNetworkGroup():
			ens = ens.filter(group=self.getNetworkGroup())
		joins = 0
		# filter statements must be limited because each one causes an 
		# additional table to be added to a join statement
		# SQLite has an internal limit of 64 tables
		for con in self.connectionSetAll():
			dev = con.interface.device
			if dev.host:
				joins = joins + 1
				ens = ens.filter(externalnetworkbridge__host=dev.host)
				if joins > 10:
					#break the loop here keeping the filtered set
					break
		if joins > 10:
			#continue the filtering manually
			enshosts = {}
			for en in ens:
				enshosts[en] = set()
				for enb in en.externalnetworkbridge_set.all():
					enshosts[en].add(enb.host)
			for con in self.connectionSetAll():
				dev = con.interface.device
				if dev.host:
					for en in enshosts.keys():
						if not dev.host in enshosts[en]:
							enshosts.remove(en)
			ens = enshosts.keys()
		for en in ens:
			options.add(en, 1.0)
		return options
		
	def _selectUsedNetwork(self):
		self.used_network = self.networkOptions().best()
		fault.check(self.used_network, "No free external network of type %s", self.getNetworkType())
		self.save()
		
	def getPrepareTasks(self):
		taskset = Connector.getPrepareTasks(self)
		taskset.add(tasks.Task("select-network", self._selectUsedNetwork))
		return self._adaptTaskset(taskset)

	def _unselectUsedNetwork(self):
		self.used_network = None
		self.save()	
	
	def getDestroyTasks(self):
		taskset = Connector.getDestroyTasks(self)
		taskset.add(tasks.Task("unselect-network", self._unselectUsedNetwork))
		return self._adaptTaskset(taskset)

	def getCapabilities(self, user):
		capabilities = Connector.getCapabilities(self, user)
		capabilities["configure"].update({
			"network_type": self.state == State.CREATED,
			"network_group": self.state == State.CREATED,
		})
		return capabilities

	def configure(self, properties):
		if self.state != State.CREATED:
			fault.check(not "network_type" in properties, "Cannot change type of external network with prepared connections: %s", self.name)
			fault.check(not "network_group" in properties, "Cannot change group of external network with prepared connections: %s", self.name)
		Connector.configure(self, properties)
		if "network_type" in properties:
			self.setNetworkType(properties["network_type"])
		if "network_group" in properties:
			self.setNetworkGroup(properties["network_group"])
		if self.getNetworkType() == "auto":
			self.setNetworkType(None)
		if self.getNetworkGroup() == "auto":
			self.setNetworkGroup(None)
		self.save()		
	
	def connectionsAdd(self, iface_name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfacesGet(iface_name)
		fault.check(iface.device.state != State.STARTED, "Cannot add connections to running device: %s -> %s", (iface_name, self.name) )
		con = Connection ()
		con.connector = self
		con.interface = iface
		con.init()
		con.save()

	def connectionsConfigure(self, iface_name, properties):
		pass
	
	def connectionsDelete(self, iface_name): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfacesGet(iface_name)
		fault.check(iface.device.state != State.STARTED, "Cannot delete connections to running devices: %s -> %s", (iface_name, self.name) )
		con = self.connectionSetGet(iface)
		con.delete()
		
	def getResourceUsage(self):
		external = 0
		traffic = 0
		for con in self.connectionSetAll():
			if con.interface.device.state == State.STARTED:
				external += 1
			dev = con.interface.device
			if dev.host and dev.state == State.STARTED:
				iface = dev.upcast().interfaceDevice(con.interface)
				try:
					traffic += ifaceutil.getRxBytes(dev.host, iface) + ifaceutil.getTxBytes(dev.host, iface) 
				except:
					traffic = -1
		return {"external": external, "traffic": traffic}		

	def getBridge(self, connection, assign=True, create=True):
		assert connection.getHost(), "Interface is not prepared: %s" % connection.interface
		for enb in self.used_network.externalnetworkbridge_set.all():
			if enb.host == connection.getHost():
				if create:
					ifaceutil.bridgeCreate(enb.host, enb.bridge)
				return enb.bridge
		assert False, "No external network bridge %s(%s) on host %s" % (self.getNetworkType(), self.getNetworkGroup(), connection.interface.device.host)
	
	def toDict(self, auth):
		res = Connector.toDict(self, auth)
		res["attrs"].update(used_network=self.used_network.toDict() if self.used_network else None, network_type=self.network_type, network_group=self.network_group)
		return res
