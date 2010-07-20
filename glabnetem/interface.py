# -*- coding: utf-8 -*-

from util import *

class Interface(XmlObject):
  
	def __init__ ( self, device, dom ):
		self.device = device
		XmlObject.decode_xml(self, dom)

	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	
	def encode_xml(self, dom, doc):
		XmlObject.encode_xml(self, dom)