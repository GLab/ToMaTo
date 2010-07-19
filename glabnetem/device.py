# -*- coding: utf-8 -*-

from interface import *
from util import *

class Device:
  
	def __init__ ( self, topology, dom ):
		self.interfaces={}
		self.topology = topology
		self.decode_xml ( dom )
		
	def add_if ( self, attributes ):
		iface = Interface(self, attributes)
		self.interfaces[iface.id] = iface 
		
	def del_if ( self, if_id ):
		del self.interfaces[if_id]
		
	def get_if ( self, if_id ):
		return self.interfaces[if_id]
		
	def decode_xml ( self, dom ):
		self.attributes = {}
		for key in dom.attributes.keys():
			self.attributes[key] = dom.attributes[key].value
		self.id = dom.getAttribute('id')
		self.type = dom.getAttribute('type')
		self.host = dom.getAttribute('host')
		for interface in dom.getElementsByTagName ( "interface" ):
			self.add_if ( interface.attributes )
