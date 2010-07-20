# -*- coding: utf-8 -*-

from util import *

class Interface(object):
  
	def __init__ ( self, device, attributes ):
		self.device = device
		self.attributes = {}
		for key in attributes.keys():
			self.attributes[key] = attributes[key].value

	def get_attr(self, name):
		if name in self.attributes:
			return self.attributes[name]
		else:
			return None	
	def set_attr(self, name, value):
		self.attributes[name]=value

	id=property(curry(get_attr, "id"), curry(set_attr, "id"))