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

class ExternalNetworkConnector(generic.Connector):
	used_network = models.ForeignKey(hosts.ExternalNetwork, null=True) 
	
	def upcast(self):
		return self

	def init(self):
		self.attributes["network_type"] = "internet"
		self.attributes["network_group"] = None

	def _update_host_preferences(self, prefs, en):
		if not en.has_free_slots():
			return
		hosts = []
		used = en.usage_count()
		if en.avoid_duplicates:
			for con in self.connection_set_all():
				dev = con.interface.device
				if dev.host:
					hosts.append(dev.host)
		for enb in en.externalnetworkbridge_set.all():
			if enb.host.enabled and not (en.avoid_duplicates and (enb.host in hosts)):
				if en.max_devices:
					prefs.add(enb.host, 1.0-used/en.max_devices)
				else:
					prefs.add(enb.host, 1.0)
		
	def host_preferences(self):
		prefs = generic.ObjectPreferences(True)
		if self.used_network:
			self._update_host_preferences(prefs, self.used_network)
		else:
			for en in self.network_options().objects:
				self._update_host_preferences(prefs, en)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def network_options(self):
		options = generic.ObjectPreferences(True)
		ens = hosts.ExternalNetwork.objects.filter(type=self.attributes["network_type"])
		if self.attributes["network_group"]:
			ens = ens.filter(group=self.attributes["network_group"])
		for con in self.connection_set_all():
			dev = con.interface.device
			if dev.host:
				ens = ens.filter(externalnetworkbridge__host=dev.host)
		for en in ens:
			options.add(en, 1.0)
		return options
		
	def start_run(self):
		generic.Connector.start_run(self)
		self.state = generic.State.STARTED
		self.save()

	def stop_run(self):
		generic.Connector.stop_run(self)
		self.state = generic.State.PREPARED
		self.save()

	def prepare_run(self):
		generic.Connector.prepare_run(self)
		self.used_network = self.network_options().best()
		if not self.used_network:
			raise fault.new(fault.NO_RESOURCES, "No free external network of type %s" % self.attributes["network_type"])
		self.state = generic.State.PREPARED
		self.save()

	def destroy_run(self):
		generic.Connector.destroy_run(self)
		self.used_network = None		
		self.state = generic.State.CREATED
		self.save()
		
	def configure(self, properties):
		if "network_type" in properties and self.state != generic.State.CREATED: 
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change type of external network with prepared connections: %s" % self.name )
		if "network_group" in properties and self.state != generic.State.CREATED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change group of external network with prepared connections: %s" % self.name )
		generic.Connector.configure(self, properties)
		if self.attributes["network_group"] == "auto":
			self.attributes["network_group"] = ""
		self.save()		
	
	def connections_add(self, iface_name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to running device: %s -> %s" % (iface_name, self.name) )
		con = generic.Connection ()
		con.init()
		con.connector = self
		con.interface = iface
		con.save()

	def connections_configure(self, iface_name, properties):
		pass
	
	def connections_delete(self, iface_name): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to running devices: %s -> %s" % (iface_name, self.name) )
		con = self.connection_set_get(iface)
		con.delete()
		
	def get_resource_usage(self):
		external = 0
		traffic = 0
		for con in self.connection_set_all():
			if con.interface.device.state == generic.State.STARTED:
				external += 1
			dev = con.interface.device
			if dev.host and dev.state == generic.State.STARTED:
				iface = dev.upcast().interface_device(con.interface)
				try:
					traffic += int(dev.host.execute("[ -f /sys/class/net/%s/statistics/rx_bytes ] && cat /sys/class/net/%s/statistics/rx_bytes || echo 0" % (iface, iface) ))
					traffic += int(dev.host.execute("[ -f /sys/class/net/%s/statistics/tx_bytes ] && cat /sys/class/net/%s/statistics/tx_bytes || echo 0" % (iface, iface) ))
				except:
					traffic = -1
		return {"external": external, "traffic": traffic}		

	def bridge_name(self, interface):
		if not interface.device.host:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE, "Interface is not prepared: %s" % interface)
		for enb in self.used_network.externalnetworkbridge_set.all():
			if enb.host == interface.device.host:
				return enb.bridge
		raise fault.Fault(fault.NO_RESOURCES, "No external network bridge %s(%s) on host %s" % (self.attributes["network_type"], self.attributes["network_group"], interface.device.host))
	
	def to_dict(self, auth):
		res = generic.Connector.to_dict(self, auth)
		res["attrs"].update(used_network=self.used_network)
		return res
