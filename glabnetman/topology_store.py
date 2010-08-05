# -*- coding: utf-8 -*-

from util import *
from config import *
from resource_store import *
from topology import *
from api import *

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

	def exists (id):
		"""
		Returns whether a topology exists
		@param id id of the topology
		"""
		return TopologyStore.topologies.has_key(id)
	exists = static(exists)

	def get (id):
		"""
		Returns a topology by its id
		@param id id of the topology
		"""
		if not TopologyStore.exists(id):
			from api import Fault
			raise Fault(Fault.NO_SUCH_TOPOLOGY, "no such topology: %s" % id) 
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
		TopologyStore.save()
		return topology.id
	add = static(add)
	
	def remove (id):
		"""
		Removes a topology by its id
		@param id id of the topology
		"""
		if not TopologyStore.exists(id):
			from api import Fault
			raise Fault(Fault.NO_SUCH_TOPOLOGY, "no such topology: %s" % id) 
		top = TopologyStore.topologies[id]
		if not top.state == TopologyState.CREATED:
			from api import Fault
			raise Fault (Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "must be stopped and destroyed")
		top.id = None
		top.free_resources()
		del TopologyStore.topologies[id]
		os.remove(Config.topology_dir+"/"+str(id)+".xml")
		TopologyStore.save()
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
