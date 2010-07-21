# -*- coding: utf-8 -*-

from util import *

class Connection(XmlObject):
  
	def __init__ ( self, connector, dom ):
		self.connector = connector
		XmlObject.decode_xml(self,dom)
		self.device = connector.topology.devices[self.device_id]
		self.interface = self.device.interfaces[self.interface_id]
		self.interface.connection = self

	def encode_xml (self, dom, doc):
		XmlObject.encode_xml(self, dom)

	bridge_name=property(curry(XmlObject.get_attr, "bridge"), curry(XmlObject.set_attr, "bridge"))
	bridge_id=property(curry(XmlObject.get_attr, "bridge_id"), curry(XmlObject.set_attr, "bridge_id"))
	device_id=property(curry(XmlObject.get_attr, "device"), curry(XmlObject.set_attr, "device"))
	interface_id=property(curry(XmlObject.get_attr, "interface"), curry(XmlObject.set_attr, "interface"))
	
	def retake_resources(self):
		if self.bridge_id:
			self.device.host.bridge_ids.take_specific(self.bridge_id)
			self.bridge_name = "gbr" + self.bridge_id

	def take_resources(self):
		if not self.bridge_id and not self.bridge_name:
			self.bridge_id = self.device.host.bridge_ids.take()
			self.bridge_name = "gbr" + self.bridge_id

	def free_resources(self):
		if self.bridge_id:
			self.device.host.bridge_ids.free(self.bridge_id)
			self.bridge_id = None
			self.bridge_name = None
