# -*- coding: utf-8 -*-

from interface import *
from util import *
from host_store import *

class Device(XmlObject):
  
	def __init__ ( self, topology, dom, load_ids ):
		self.interfaces={}
		self.topology = topology
		Device.decode_xml ( self, dom, load_ids )
		try:
			self.host = HostStore.get(self.host_name)
		except KeyError:
			raise Exception("Unknown host: %s" % self.host_name)
		
	def add_if ( self, iface ):
		self.interfaces[iface.id] = iface
		
	def del_if ( self, if_id ):
		del self.interfaces[if_id]
		
	def get_if ( self, if_id ):
		return self.interfaces[if_id]
	
	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	type=property(curry(XmlObject.get_attr, "type"), curry(XmlObject.set_attr, "type"))
	host_name=property(curry(XmlObject.get_attr, "host"), curry(XmlObject.set_attr, "host"))

	def decode_xml ( self, dom, load_ids ):
		XmlObject.decode_xml(self,dom)
		for interface in dom.getElementsByTagName ( "interface" ):
			self.add_if ( Interface(self,interface, load_ids) )

	def encode_xml ( self, dom, doc, print_ids ):
		XmlObject.encode_xml(self,dom)
		for interface in self.interfaces.values():
			iface = doc.createElement("interface")
			interface.encode_xml(iface,doc, print_ids)
			dom.appendChild(iface)
