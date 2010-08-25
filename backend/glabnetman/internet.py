# -*- coding: utf-8 -*-

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
	