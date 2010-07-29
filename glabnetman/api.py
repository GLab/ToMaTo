# -*- coding: utf-8 -*-

from host_store import *
from host import *
from topology_store import *
from topology import *

class TopologyInfo():
	def __init__(self, topology):
		self.id = topology.id
		self.state = str(topology.state)
		self.owner = str(topology.owner)

class HostInfo():
	def __init__(self, host):
		self.name = host.name

class PublicAPI():
	def __init__(self):
		pass
	
	def top_info(self, id, username=None):
		return TopologyInfo(TopologyStore.get(id))

	def top_list(self, filter_owner=None, filter_state=None, username=None):
		tops=[]
		for t in TopologyStore.topologies.values():
			if filter_state==None or t.state==filter_state:
				tops.append(TopologyInfo(t))
		return tops
	
	def top_import(self, xml, username=None):
		dom=minidom.parseString(xml)
		top=Topology(dom,False)
		top.owner=username
		id=TopologyStore.add(top)
		return id
	
	def top_remove(self, top_id, username=None):
		TopologyStore.remove(top_id)
		return True
	
	def top_prepare(self, top_id, username=None):
		TopologyStore.get(top_id).prepare()
		return True
	
	def top_destroy(self, top_id, username=None):
		TopologyStore.get(top_id).destroy()
		return True
	
	def top_upload(self, top_id, username=None):
		TopologyStore.get(top_id).upload()
		return True
	
	def top_start(self, top_id, username=None):
		TopologyStore.get(top_id).start()
		return True
	
	def top_stop(self, top_id, username=None):
		TopologyStore.get(top_id).stop()
		return True
	
	def top_get(self, top_id, include_ids=False, username=None):
		top=TopologyStore.get(top_id)
		dom=top.create_dom(include_ids)
		return dom.toprettyxml(indent="\t", newl="\n")
		
	def host_list(self, username=None):
		hosts=[]
		for h in HostStore.hosts.values():
			hosts.append(HostInfo(h))
		return hosts

	def host_add(self, host_name, username=None):
		host=Host(host_name)
		host.check()
		HostStore.add(host)
		return True

	def host_remove(self, host_name, username=None):
		HostStore.remove(host_name)
		return True
