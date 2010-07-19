# -*- coding: utf-8 -*-

class Connector:
  
	def __init__ ( self, topology, dom ):
		self.connections=set()
		self.topology = topology
		self.decode_xml ( dom )

	def add_if ( self, interface ):
		self.connections.add ( interface )
		
	def del_if ( self, interface ):
		self.connections.remove ( interface )
		
	def decode_xml ( self, dom ):
		self.attributes = {}
		for key in dom.attributes.keys():
			self.attributes[key] = dom.attributes[key].value
		self.id = dom.getAttribute('id')
		self.type = dom.getAttribute('type')
		for connection in dom.getElementsByTagName ( "connection" ):
			device = connection.getAttribute('device')
			interface = connection.getAttribute('interface')
			self.add_if ( self.topology.devices[device].get_if(interface) )
