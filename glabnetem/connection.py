# -*- coding: utf-8 -*-

from util import *

class Connection(XmlObject):
  
	def __init__ ( self, connector, dom ):
		self.connector = connector
		XmlObject.decode_xml(self,dom)
		self.device = connector.topology.devices[self.device_id]
		self.interface = self.device.interfaces[self.interface_id]

	def encode_xml (self, dom, doc):
		XmlObject.encode_xml(self, dom)
		
	device_id=property(curry(XmlObject.get_attr, "device"), curry(XmlObject.set_attr, "device"))
	interface_id=property(curry(XmlObject.get_attr, "interface"), curry(XmlObject.set_attr, "interface"))