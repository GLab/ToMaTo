# -*- coding: utf-8 -*-

import generic, fault

class InternetConnector(generic.Connector):

	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.save()		
		for connection in dom.getElementsByTagName ( "connection" ):
			con = generic.Connection()
			con.init (self, connection)
			con.bridge_special_name = con.interface.device.host.public_bridge
			self.connection_set.add ( con )

	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Connector.encode_xml(self, dom, doc, internal)
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)
		
	def write_aux_files(self):
		pass
	
	def write_control_script(self, host, script, fd):
		pass
		
	def change_possible(self, dom):
		raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Changes of internet connectors not implemented yet")
	
	def change_run(self, dom, task):
		#FIXME: replace/add connections
		pass