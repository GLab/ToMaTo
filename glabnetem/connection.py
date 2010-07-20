# -*- coding: utf-8 -*-

class Connection(object):
  
	def __init__ ( self, connector, iface, attributes ):
		self.connector = connector
		self.interface = iface
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
