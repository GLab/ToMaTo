# -*- coding: utf-8 -*-

class TopologyStore:

	topologies = {}

	def __init__ (self):
		pass
	
	def get (self, id):
		return topologies[id]
	
	def add (self, topology):
		topologies[topology.id] = topology
		return topology.id
	
	def remove (self, id):
		del topologies[id] 
		
	def load (self):
		pass
	
	def save (self):
		pass