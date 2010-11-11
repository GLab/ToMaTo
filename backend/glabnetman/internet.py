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

import generic, fault

class InternetConnector(generic.Connector):

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
		ips = 0
		for con in self.connections_all():
			if con.interface.device.state == generic.State.STARTED:
				ips += 1
		return {"disk": 0, "memory": 0, "ports": 0, "public_ips": ips}		
