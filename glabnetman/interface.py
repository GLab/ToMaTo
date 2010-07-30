# -*- coding: utf-8 -*-

from util import *

class Interface(XmlObject):
  	"""
	This class represents an interface
	"""

	def __init__ ( self, device, dom, load_ids ):
		"""
		Creates an interface object
		@param device the parent device object
		@param dom the xml dom object of the interface
		@param load_ids whether to lod or ignore assigned ids
		"""
		self.device = device
		self.connection = None
		XmlObject.decode_xml(self, dom)

	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	
	def encode_xml(self, dom, doc, print_ids):
		"""
		Encode the object to an xml dom object
		@param dom the xml dom object to write the data to
		@param doc the xml document needed to create child elements
		@print_ids whether to include or ignore assigned ids
		"""
		XmlObject.encode_xml(self, dom)
	
	def __repr__(self):
		return self.device.id + "." + self.id