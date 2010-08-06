# -*- coding: utf-8 -*-

from util import *
import config, api
from resource_store import *
from topology import *

from xml.dom import minidom

import atexit, os

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
	return topologies.has_key(id)

def get (id):
	"""
	Returns a topology by its id
	@param id id of the topology
	"""
	if not exists(id):
		raise api.Fault(api.Fault.NO_SUCH_TOPOLOGY, "no such topology: %s" % id) 
	return topologies[id]
	
def add_id (topology):
	"""
	Adds a given topology using the id that it specifies
	@param topology the topology to add
	"""
	ids.take_specific(int(topology.id))
	topology.retake_resources()
	topologies[int(topology.id)] = topology
	return topology.id

def add (topology):
	"""
	Adds a given topology using the next free id
	@param topology the topology to add
	"""
	topology.id = str(ids.take())
	topology.take_resources()
	topologies[int(topology.id)] = topology
	save()
	return topology.id
	
def remove (id):
	"""
	Removes a topology by its id
	@param id id of the topology
	"""
	if not exists(id):
		raise api.Fault(api.Fault.NO_SUCH_TOPOLOGY, "no such topology: %s" % id) 
	top = topologies[id]
	if not top.state == TopologyState.CREATED:
		raise api.Fault (api.Fault.INVALID_TOPOLOGY_STATE_TRANSITION, "must be stopped and destroyed")
	top.id = None
	top.free_resources()
	del topologies[id]
	os.remove(config.topology_dir+"/"+str(id)+".xml")
	save()
		
def load():
	"""
	Loads all topologies in this store
	"""
	if not os.path.exists(config.topology_dir):
		return
	for file in os.listdir(config.topology_dir):
		add_id ( Topology(minidom.parse(config.topology_dir+"/"+file), True) )
	for top in topologies.values():
		top.take_resources()
		
def save():
	"""
	Saves all topologies to files
	"""
	if not os.path.exists(config.topology_dir):
		os.makedirs(config.topology_dir)
	for top in topologies.values():
		top.save_to(config.topology_dir+"/"+top.id+".xml",True)

def init():
	load()
	atexit.register(save)
