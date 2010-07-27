# -*- coding: utf-8 -*-

from util import *
from config import *
from resource_store import *
from topology import *

from xml.dom import minidom

import atexit, os

class TopologyStore(object):
	"""
	A topology store holds all topologes that glabnetman knows of.
	The store is automatically loaded and saved to a file configured in the configuration but it helps to call save() after changes.
	The topologies are stored in individual xml files in a configures directory.
	"""
	
	topologies = {}
	ids = ResourceStore ( 1, 10000 )

	def get (id):
		"""
		Returns a topology by its id
		@param id id of the topology
		"""
		return TopologyStore.topologies[id]
	get = static(get)
	
	def add_id (topology):
		"""
		Adds a given topology using the id that it specifies
		@param topology the topology to add
		"""
		TopologyStore.ids.take_specific(int(topology.id))
		topology.retake_resources()
		TopologyStore.topologies[int(topology.id)] = topology
		return topology.id
	add_id = static(add_id)

	def add (topology):
		"""
		Adds a given topology using the next free id
		@param topology the topology to add
		"""
		topology.id = str(TopologyStore.ids.take())
		topology.take_resources()
		TopologyStore.topologies[int(topology.id)] = topology
		return topology.id
	add = static(add)
	
	def remove (id):
		"""
		Removes a topology by its id
		@param id id of the topology
		"""
		top = TopologyStore.topologies[id]
		top.id = None
		top.free_resources()
		del TopologyStore.topologies[id]
		os.remove(Config.topology_dir+"/"+str(id)+".xml")
	remove = static(remove)
		
	def load():
		"""
		Loads all topologies in this store
		"""
		if not os.path.exists(Config.topology_dir):
			return
		for file in os.listdir(Config.topology_dir):
			TopologyStore.add_id ( Topology(minidom.parse(Config.topology_dir+"/"+file), True) )
		for top in TopologyStore.topologies.values():
			top.take_resources()
	load = static(load)
		
	def save():
		"""
		Saves all topologies to files
		"""
		if not os.path.exists(Config.topology_dir):
			os.makedirs(Config.topology_dir)
		for top in TopologyStore.topologies.values():
			top.save_to(Config.topology_dir+"/"+top.id+".xml",True)
	save = static(save)

TopologyStore.load()
atexit.register(TopologyStore.save)
