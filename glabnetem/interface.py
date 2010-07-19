# -*- coding: utf-8 -*-

class Interface:
  
	def __init__ ( self, device, attributes ):
		self.device = device
		self.attributes = {}
		for key in attributes.keys():
			self.attributes[key] = attributes[key].value
		self.id = self.attributes["id"]