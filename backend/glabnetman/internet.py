# -*- coding: utf-8 -*-

import generic

class InternetConnector(generic.Connector):

	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.save()		
		for connection in dom.getElementsByTagName ( "connection" ):
			con = generic.Connection()
			con.init (self, connection)
			self.connection_set.add ( con )

	def encode_xml(self, dom, doc, internal):
		pass
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)
		
	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass
		