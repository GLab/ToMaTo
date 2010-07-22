# -*- coding: utf-8 -*-

from util import *

class Interface(XmlObject):
  
	def __init__ ( self, device, dom, load_ids ):
		self.device = device
		self.connection = None
		XmlObject.decode_xml(self, dom)

	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	
	def encode_xml(self, dom, doc, print_ids):
		XmlObject.encode_xml(self, dom)