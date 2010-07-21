# -*- coding: utf-8 -*-

from util import *
from config import *
from resource_store import *
from topology import *

import atexit, os

class TopologyStore(object):

	topologies = {}
	ids = ResourceStore ( 1, 10000 )

	def get (id):
		return TopologyStore.topologies[id]
	get = static(get)
	
	def add_id (topology):
		TopologyStore.ids.take_specific(int(topology.id))
		TopologyStore.topologies[int(topology.id)] = topology
		return topology.id
	add_id = static(add_id)

	def add (topology):
		topology.id = str(TopologyStore.ids.take())
		TopologyStore.topologies[int(topology.id)] = topology
		return topology.id
	add = static(add)
	
	def remove (id):
		top = TopologyStore.topologies[id]
		top.id = None
		top.free_resources()
		del TopologyStore.topologies[id]
		os.remove(Config.topology_dir+"/"+str(id)+".xml")
	remove = static(remove)
		
	def load():
		if not os.path.exists(Config.topology_dir):
			return
		for file in os.listdir(Config.topology_dir):
			TopologyStore.add_id ( Topology(Config.topology_dir+"/"+file) )
	load = static(load)
		
	def save():
		if not os.path.exists(Config.topology_dir):
			os.makedirs(Config.topology_dir)
		for top in TopologyStore.topologies.values():
			top.save_to(Config.topology_dir+"/"+top.id+".xml")
	save = static(save)

TopologyStore.load()
atexit.register(TopologyStore.save)
