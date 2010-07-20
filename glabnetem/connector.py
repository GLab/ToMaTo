# -*- coding: utf-8 -*-

from connection import *
from util import *

class Connector(XmlObject):
  
	def __init__ ( self, topology, dom ):
		self.connections=set()
		self.topology = topology
		self.decode_xml ( dom )

	def add_con ( self, con ):
		self.connections.add ( con )
		
	def del_con ( self, con ):
		self.connections.remove ( con )
		
	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	type=property(curry(XmlObject.get_attr, "type"), curry(XmlObject.set_attr, "type"))
	
	def decode_xml ( self, dom ):
		XmlObject.decode_xml(self,dom)
		for connection in dom.getElementsByTagName ( "connection" ):
			self.add_con ( Connection(self, connection) )

	def encode_xml ( self, dom, doc ):
		XmlObject.encode_xml(self,dom)
		for con in self.connections:
			x_con = doc.createElement("connection")
			con.encode_xml (x_con, doc)
			dom.appendChild(x_con)
