# -*- coding: utf-8 -*-

from xml.dom import minidom

from util import *
from host import *
from topology import TopologyState

import topology_store, config, api

import atexit, os

"""
A global storage for host objects. It contains all availabe hosts.
The store is automatically loaded and saved to a file configured in the configuration but it helps to call save() after changes.
The hosts are stored in that file using a simple xml format:
<hosts>
	<host name="hostname1"/>
	<host name="hostname1"/>
	...
</hosts>
"""
hosts = {}
groups = {}
	
def load ():
	"""
	Load hosts from file
	"""
	if not os.path.exists ( config.hosts ):
		return
	dom = minidom.parse ( config.hosts )
	x_hosts = dom.getElementsByTagName ( "hosts" )[0]
	for x_host in x_hosts.getElementsByTagName ( "host" ):
		host = Host ()
		host.decode_xml(x_host)
		add ( host )
			
def save ():
	"""
	Save hosts to file
	"""
	doc = minidom.Document()
	x_hosts = doc.createElement ( "hosts" )
	doc.appendChild ( x_hosts )
	for host in hosts.values():
		x_host = doc.createElement ( "host" )
		host.encode_xml(x_host)
		x_hosts.appendChild ( x_host )
	fd = open ( config.hosts, "w" )
	doc.writexml(fd, indent="", addindent="\t", newl="\n")
	fd.close()

def add(host):
	"""
	Add a host to the host store
	@param host to store
	"""
	if exists(host.name):
		raise api.Fault(api.Fault.HOST_EXISTS, "host exists: %s" % host.name)
	hosts[str(host.name)] = host
	if not groups.has_key(host.group):
		groups[host.group] = set()
	groups[host.group].add(host)
	save()
		
def exists(host_name):
	"""
	Check whether a host exists
	@param host_name name of the host to find
	"""
	return hosts.has_key(str(host_name))

def group_exists(group_name):
	"""
	Check whether a host group exists
	@param group_name name of the group to find
	"""
	return groups.has_key(str(group_name))

def get(host_name):
	"""
	Retrieve a host by its name
	@param host_name name of the host to find
	"""
	if not exists(host_name):
		raise api.Fault(api.Fault.NO_SUCH_HOST, "no such host: %s" % host_name)
	return hosts[str(host_name)]
		
def get_group(group_name):
	"""
	Retrieve all hosts of a group
	@param host_group name of the host group
	"""
	if not group_exists(group_name):
		raise api.Fault(api.Fault.NO_SUCH_HOST_GROUP, "no such host group: %s" % group_name)
	return groups[str(group_name)]

def group_list():
	"""
	Retrieve all host groups
	"""
	return groups.key_set()

def remove(host_name):
	"""
	Remove a host from the host store
	@param host_name name of the host to remove
	"""
	if not exists(host_name):
		raise api.Fault(api.Fault.NO_SUCH_HOST, "no such host: %s" % host_name)
	host = hosts[host_name]
	del hosts[host_name]
	groups[host.group].remove(host)
	if groups[host.group] == set():
		del groups[host.group]
	save()
	
def select_host(group=None):
	best = None
	if group:
		thosts = get_group(group)
	else:
		thosts = hosts.values()
	for host in thosts:
		if ( not best ) or ( len(best.devices) > len(host.devices) ):
			best = host
	return best

def check_add(host, task):
	task.subtasks_total = 5
	host.check(task)
	add(host)
	task.done()

def init():
	load()
	atexit.register(save)