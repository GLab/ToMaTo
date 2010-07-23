# -*- coding: utf-8 -*-

from connection import *
from util import *

class Connector(XmlObject):
  
	def __init__ ( self, topology, dom, load_ids ):
		self.connections=set()
		self.topology = topology
		Connector.decode_xml ( self, dom, load_ids )

	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	type=property(curry(XmlObject.get_attr, "type"), curry(XmlObject.set_attr, "type"))
	
	def decode_xml ( self, dom, load_ids ):
		XmlObject.decode_xml(self,dom)
		for connection in dom.getElementsByTagName ( "connection" ):
			self.connections.add ( Connection(self, connection, load_ids) )

	def encode_xml ( self, dom, doc, print_ids ):
		XmlObject.encode_xml(self,dom)
		for con in self.connections:
			x_con = doc.createElement("connection")
			con.encode_xml (x_con, doc, print_ids)
			dom.appendChild(x_con)
