# -*- coding: utf-8 -*-

class ResourceStore(object):
	"""
	A resource store manages a set of resource ids
	"""
	
	def __init__ (self, start_id, num):
		"""
		Creates a new resource store
		@start_id lowest id in the resource set
		@num number of ids to insert into the resource set
		"""
		self.resources = range(start_id, start_id+num-1)
	
	def take (self):
		"""
		Takes the first free resource id.
		If all ids are taken this raises an exception.
		"""
		if len(self.resources) == 0 :
			raise Exception("no resources free")
		obj = self.resources[0]
		self.resources.remove(obj)
		return str(obj)
		
	def take_specific (self,obj):
		"""
		Takes a specific resource id.
		If this id is taken this raises an exception.
		"""
		self.resources.remove(int(obj))
		return str(obj)

	def free (self, obj):
		"""
		Frees a resource id.
		"""
		self.resources.append(int(obj))