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

	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.state = generic.State.STARTED
		self.save()		
		for connection in dom.getElementsByTagName ( "connection" ):
			self.add_connection(connection)
		
	def add_connection(self, dom):
		con = generic.Connection()
		con.init (self, dom)
		con.bridge_special_name = con.interface.device.host.public_bridge
		self.connection_set.add ( con )
		self.save()
		return con

	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Connector.encode_xml(self, dom, doc, internal)
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)
		
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

	def change_possible(self, dom):
		pass
	