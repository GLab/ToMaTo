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
import generic, fault, hosts

from lib import ifaceutil

class ExternalNetworkConnector(generic.Connector):
	used_network = models.ForeignKey(hosts.ExternalNetwork, null=True) 
	
	def upcast(self):
		return self

	def init(self):
		self.setNetworkType("internet")
		self.setNetworkGroup("")

	def getNetworkType(self):
		return self.attributes["network_type"]
	
	def setNetworkType(self, value):
		self.attributes["network_type"] = value

	def getNetworkGroup(self):
		return self.attributes["network_group"]
	
	def setNetworkGroup(self, value):
		self.attributes["network_group"] = value

	def _updateHostPreferences(self, prefs, en):
		if not en.has_free_slots():
			return
		hosts = []
		used = en.usage_count()
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
		prefs = generic.ObjectPreferences(True)
		if self.used_network:
			self._updateHostPreferences(prefs, self.used_network)
		else:
			for en in self.networkOptions().objects:
				self._updateHostPreferences(prefs, en)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def networkOptions(self):
		options = generic.ObjectPreferences(True)
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
		assert self.used_network, "No free external network of type %s" % self.attributes["network_type"]
		self.save()
		
	def getPrepareTasks(self):
		import tasks
		taskset = generic.Connector.getPrepareTasks(self)
		taskset.addTask(tasks.Task("select-network", self._selectUsedNetwork))
		return taskset

	def _unselectUsedNetwork(self):
		self.used_network = None
		self.save()	
	
	def getDestroyTasks(self):
		import tasks
		taskset = generic.Connector.getDestroyTasks(self)
		taskset.addTask(tasks.Task("unselect-network", self._unselectUsedNetwork))
		return taskset

	def configure(self, properties):
		if "network_type" in properties and self.state != generic.State.CREATED: 
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change type of external network with prepared connections: %s" % self.name )
		if "network_group" in properties and self.state != generic.State.CREATED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change group of external network with prepared connections: %s" % self.name )
		generic.Connector.configure(self, properties)
		if self.attributes["network_group"] == "auto":
			self.attributes["network_group"] = ""
		self.save()		
	
	def connectionsAdd(self, iface_name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to running device: %s -> %s" % (iface_name, self.name) )
		con = generic.Connection ()
		con.init()
		con.connector = self
		con.interface = iface
		con.save()

	def connectionsConfigure(self, iface_name, properties):
		pass
	
	def connectionsDelete(self, iface_name): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to running devices: %s -> %s" % (iface_name, self.name) )
		con = self.connectionSetGet(iface)
		con.delete()
		
	def getResourceUsage(self):
		external = 0
		traffic = 0
		for con in self.connectionSetAll():
			if con.interface.device.state == generic.State.STARTED:
				external += 1
			dev = con.interface.device
			if dev.host and dev.state == generic.State.STARTED:
				iface = dev.upcast().interface_device(con.interface)
				try:
					traffic += ifaceutil.getRxBytes(dev.host, iface) + ifaceutil.getTxBytes(dev.host, iface) 
				except:
					traffic = -1
		return {"external": external, "traffic": traffic}		

	def bridgeName(self, interface):
		if not interface.device.host:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE, "Interface is not prepared: %s" % interface)
		for enb in self.used_network.externalnetworkbridge_set.all():
			if enb.host == interface.device.host:
				return enb.bridge
		raise fault.Fault(fault.NO_RESOURCES, "No external network bridge %s(%s) on host %s" % (self.attributes["network_type"], self.attributes["network_group"], interface.device.host))
	
	def toDict(self, auth):
		res = generic.Connector.toDict(self, auth)
		res["attrs"].update(used_network=self.used_network)
		return res
