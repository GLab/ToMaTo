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

class SpecialFeatureConnector(generic.Connector):
	feature_type = models.CharField(max_length=50)
	feature_group = models.CharField(max_length=50, blank=True)
	used_feature_group = models.ForeignKey(hosts.SpecialFeatureGroup, null=True) 

	def upcast(self):
		return self

	def _update_host_preferences(self, prefs, sfg):
		if not sfg.has_free_slots():
			return
		hosts = []
		used = sfg.usage_count()
		if sfg.avoid_duplicates:
			for con in self.connection_set_all():
				dev = con.interface.device
				if dev.host:
					hosts.append(dev.host)
		for sf in sfg.specialfeature_set.all():
			if sf.host.enabled and not (sfg.avoid_duplicates and (sf.host in hosts)):
				if sfg.max_devices:
					prefs.add(sf.host, 1.0-used/sfg.max_devices)
				else:
					prefs.add(sf.host, 1.0)
		
	def host_preferences(self):
		prefs = generic.ObjectPreferences(True)
		if self.used_feature_group:
			self._update_host_preferences(prefs, self.used_feature_group)
		else:
			for sfg in self.feature_options().objects:
				self._update_host_preferences(prefs, sfg)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def feature_options(self):
		options = generic.ObjectPreferences(True)
		sfgs = hosts.SpecialFeatureGroup.objects.filter(feature_type=self.feature_type)
		if self.feature_group:
			sfgs = sfgs.filter(group_name=self.feature_group)
		for con in self.connection_set_all():
			dev = con.interface.device
			if dev.host:
				sfgs = sfgs.filter(specialfeature__host=dev.host)
		for sfg in sfgs:
			options.add(sfg, 1.0)
		return options
		
	def start_run(self, task):
		generic.Connector.start_run(self, task)
		self.state = generic.State.STARTED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Connector.stop_run(self, task)
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Connector.prepare_run(self, task)
		self.used_feature_group = self.feature_options().best()
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Connector.destroy_run(self, task)
		self.used_feature_group = None		
		self.state = generic.State.CREATED
		self.save()
		task.subtasks_done = task.subtasks_done + 1
		
	def configure(self, properties, task):
		generic.Connector.configure(self, properties, task)
		if "feature_type" in properties:
			if self.state == generic.State.CREATED:
				self.feature_type = properties["feature_type"]
			else:
				raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change type of special feature with prepared connections: %s" % self.name )
		if "feature_group" in properties:
			if self.state == generic.State.CREATED:
				self.feature_group = properties["feature_group"]
				if self.feature_group == "auto":
					self.feature_group = ""
			else:
				raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change group of special feature with prepared connections: %s" % self.name )
		self.save()		
	
	def connections_add(self, iface_name, properties, task): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to running device: %s -> %s" % (iface_name, self.name) )
		con = generic.Connection ()
		con.connector = self
		con.interface = iface
		con.save()

	def connections_configure(self, iface_name, properties, task):
		pass
	
	def connections_delete(self, iface_name, task): #@UnusedVariable, pylint: disable-msg=W0613
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to running devices: %s -> %s" % (iface_name, self.name) )
		con = self.connection_set_get(iface)
		con.delete()
		
	def get_resource_usage(self):
		special = 0
		traffic = 0
		for con in self.connection_set_all():
			if con.interface.device.state == generic.State.STARTED:
				special += 1
			dev = con.interface.device
			if dev.host and dev.state == generic.State.STARTED:
				iface = dev.upcast().interface_device(con.interface)
				traffic += int(dev.host.get_result("[ -f /sys/class/net/%s/statistics/rx_bytes ] && cat /sys/class/net/%s/statistics/rx_bytes || echo 0" % (iface, iface) ))
				traffic += int(dev.host.get_result("[ -f /sys/class/net/%s/statistics/tx_bytes ] && cat /sys/class/net/%s/statistics/tx_bytes || echo 0" % (iface, iface) ))
		return {"special": special, "traffic": traffic}		

	def bridge_name(self, interface):
		if not interface.device.host:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE, "Interface is not prepared: %s" % interface)
		for sf in self.used_feature_group.specialfeature_set.all():
			if sf.host == interface.device.host:
				return sf.bridge
		raise fault.Fault(fault.NO_RESOURCES, "No special feature %s(%s) on host %s" % (self.feature_type, self.feature_group, interface.device.host))
	
	def to_dict(self, auth):
		res = generic.Connector.to_dict(self, auth)
		res["attrs"].update(feature_type=self.feature_type, feature_group=self.feature_group, used_feature_group=self.used_feature_group)
		return res
