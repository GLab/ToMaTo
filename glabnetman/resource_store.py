# -*- coding: utf-8 -*-

class ResourceStore(object):

	def __init__ (self, start_id, num):
		self.resources = range(start_id, start_id+num-1)
	
	def take (self):
		if len(self.resources) == 0 :
			raise Exception("no resources free")
		obj = self.resources[0]
		self.resources.remove(obj)
		return str(obj)
		
	def take_specific (self,obj):
		self.resources.remove(int(obj))
		return str(obj)

	def free (self, obj):
		self.resources.append(int(obj))