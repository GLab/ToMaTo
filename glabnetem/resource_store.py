# -*- coding: utf-8 -*-

class ResourceStore(object):
		
	def __init__ (self, res):
		self.resources = res
		
	def __init__ (self, start_id, num):
		self.resources = range(start_id, start_id+num-1)
	
	host_ports = {}
	topology_ids = None

	def take (self):
		obj = self.resources[0]
		self.resources.remove(obj)
		return obj
		
	def free (self, obj):
		self.resources.add(obj)