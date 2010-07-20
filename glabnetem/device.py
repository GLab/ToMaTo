# -*- coding: utf-8 -*-

from interface import *
from util import *

class Device(object):
  
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
	
	def get_attr(self, name):
		if name in self.attributes:
			return self.attributes[name]
		else:
			return None	
	def set_attr(self, name, value):
		self.attributes[name]=value

	id=property(curry(get_attr, "id"), curry(set_attr, "id"))
	type=property(curry(get_attr, "type"), curry(set_attr, "type"))
	host=property(curry(get_attr, "host"), curry(set_attr, "host"))

	def decode_xml ( self, dom ):
		self.attributes = {}
		for key in dom.attributes.keys():
			self.attributes[key] = dom.attributes[key].value
		for interface in dom.getElementsByTagName ( "interface" ):
			self.add_if ( interface.attributes )

	def encode_xml ( self, dom, doc ):
		for key in self.attributes.keys():
			dom.setAttribute (key, self.attributes[key])
		for ikey in self.interfaces.keys():
			iface = doc.createElement("interface")
			for key in self.interfaces[ikey].attributes.keys():
				iface.setAttribute(key, self.interfaces[ikey].attributes[key])
			iface.setAttribute("id", self.interfaces[ikey].id)
			dom.appendChild(iface)
