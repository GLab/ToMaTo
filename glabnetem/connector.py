# -*- coding: utf-8 -*-

from connection import *

class Connector:
  
	def __init__ ( self, topology, dom ):
		self.connections=set()
		self.topology = topology
		self.decode_xml ( dom )

	def add_con ( self, interface, attributes ):
		self.connections.add ( Connection ( self, interface, attributes ) )
		
	def del_con ( self, con ):
		self.connections.remove ( con )
		
	def decode_xml ( self, dom ):
		self.attributes = {}
		for key in dom.attributes.keys():
			self.attributes[key] = dom.attributes[key].value
		self.id = dom.getAttribute('id')
		self.type = dom.getAttribute('type')
		for connection in dom.getElementsByTagName ( "connection" ):
			device = connection.getAttribute('device')
			interface = connection.getAttribute('interface')
			self.add_con ( self.topology.devices[device].get_if(interface), connection.attributes )

	def encode_xml ( self, dom, doc ):
		for key in self.attributes.keys():
			dom.setAttribute (key, self.attributes[key])
		dom.setAttribute("id", self.id)
		dom.setAttribute("type", self.type)
		for con in self.connections:
			x_con = doc.createElement("connection")
			for key in con.attributes.keys():
				x_con.setAttribute(key, con.attributes[key])
			x_con.setAttribute("device", con.interface.device.id)
			x_con.setAttribute("interface", con.interface.id)
			dom.appendChild(x_con)
