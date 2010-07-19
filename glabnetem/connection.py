# -*- coding: utf-8 -*-

class Connection:
  
	def __init__ ( self, connector, iface, attributes ):
		self.connector = connector
		self.interface = iface
		self.attributes = {}
		for key in attributes.keys():
			self.attributes[key] = attributes[key].value