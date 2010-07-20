# -*- coding: utf-8 -*-

from connection import *
from util import *

class Connector(object):
  
	def __init__ ( self, topology, dom ):
		self.connections=set()
		self.topology = topology
		self.decode_xml ( dom )

	def add_con ( self, interface, attributes ):
		self.connections.add ( Connection ( self, interface, attributes ) )
		
	def del_con ( self, con ):
		self.connections.remove ( con )
		
	def get_attr(self, name):
		if name in self.attributes:
			return self.attributes[name]
		else:
			return None	
	def set_attr(self, name, value):
		self.attributes[name]=value

	id=property(curry(get_attr, "id"), curry(set_attr, "id"))
	type=property(curry(get_attr, "type"), curry(set_attr, "type"))
	
	def decode_xml ( self, dom ):
		self.attributes = {}
		for key in dom.attributes.keys():
			self.attributes[key] = dom.attributes[key].value
		for connection in dom.getElementsByTagName ( "connection" ):
			device = connection.getAttribute('device')
			interface = connection.getAttribute('interface')
			self.add_con ( self.topology.devices[device].get_if(interface), connection.attributes )

	def encode_xml ( self, dom, doc ):
		for key in self.attributes.keys():
			dom.setAttribute (key, self.attributes[key])
		for con in self.connections:
			x_con = doc.createElement("connection")
			for key in con.attributes.keys():
				x_con.setAttribute(key, con.attributes[key])
			x_con.setAttribute("device", con.interface.device.id)
			x_con.setAttribute("interface", con.interface.id)
			dom.appendChild(x_con)
