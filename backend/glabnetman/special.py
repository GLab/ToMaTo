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
import generic, fault

class SpecialFeatureConnector(generic.Connector):
	feature_type = models.CharField(max_length=50)
	feature_group = models.CharField(max_length=50, blank=True)

	def add_connection(self, dom):
		con = generic.Connection()
		con.init (self, dom)
		self.connection_set.add ( con )
		self.save()
		return con

	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Connector.encode_xml(self, dom, doc, internal)
		dom.setAttribute("feature_type", self.feature_type)
		if self.feature_group:
			dom.setAttribute("feature_group", self.feature_group)
		
	def start_run(self, task):
		generic.Connector.start_run(self, task)
		#not changing state
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Connector.stop_run(self, task)
		#not changing state
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Connector.prepare_run(self, task)
		#not changing state
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Connector.destroy_run(self, task)		
		#not changing state
		task.subtasks_done = task.subtasks_done + 1
		
	def configure(self, properties, task):
		generic.Connector.configure(self, properties, task)
		fixed = False
		for c in self.connections_all():
			if c.interface:
				dev = c.interface.device
				if dev.state == generic.State.PREPARED or dev.state == generic.State.STARTED:
					fixed = True
		if "feature_type" in properties:
			if fixed:
				raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change type of special feature with prepared connections: %s" % self.name )
			else:
				self.feature_type = properties["feature_type"]
		if "feature_group" in properties:
			if fixed:
				raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot change group of special feature with prepared connections: %s" % self.name )
			else:
				self.feature_group = properties["feature_group"]
		self.save()		
				
	def connections_add(self, iface_name, properties, task):
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to running device: %s -> %s" % (iface_name, self.name) )
		con = generic.Connection ()
		con.connector = self
		con.interface = iface
		con.save()

	def connections_configure(self, iface_name, properties, task):
		pass
	
	def connections_delete(self, iface_name, task):
		iface = self.topology.interfaces_get(iface_name)
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to running devices: %s -> %s" % (iface_name, self.name) )
		con = self.connections_get(iface)
		con.delete()

	def get_resource_usage(self):
		special = 0
		for con in self.connections_all():
			if con.interface.device.state == generic.State.STARTED:
				special += 1
		return {"disk": 0, "memory": 0, "ports": 0, "special": special}		

	def bridge_name(self, interface):
		if not interface.device.host:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE, "Interface is not prepared: %s" % interface)
		for sf in interface.device.host.special_features():
			if sf.feature_type == self.feature_type and (not self.feature_group or sf.feature_group == self.feature_group):
				return sf.bridge
		raise fault.Fault(fault.NO_RESOURCES, "No special feature %s(%s) on host %s" % (self.feature_type, self.feature_group, interface.device.host))