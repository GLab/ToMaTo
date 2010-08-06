# -*- coding: utf-8 -*-

from xml.dom import minidom

from util import *
from config import *
from host import *
from api import *

import atexit, os

class HostStore(object):
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
		if not os.path.exists ( Config.hosts ):
			return
		dom = minidom.parse ( Config.hosts )
		x_hosts = dom.getElementsByTagName ( "hosts" )[0]
		for x_host in x_hosts.getElementsByTagName ( "host" ):
			host = Host ()
			host.decode_xml(x_host)
			HostStore.add ( host )
	load = static(load)
			
	def save ():
		"""
		Save hosts to file
		"""
		doc = minidom.Document()
		x_hosts = doc.createElement ( "hosts" )
		doc.appendChild ( x_hosts )
		for host in HostStore.hosts.values():
			x_host = doc.createElement ( "host" )
			host.encode_xml(x_host)
			x_hosts.appendChild ( x_host )
		fd = open ( Config.hosts, "w" )
		doc.writexml(fd, indent="", addindent="\t", newl="\n")
		fd.close()
	save = static(save)

	def add(host):
		"""
		Add a host to the host store
		@param host to store
		"""
		if HostStore.exists(host.name):
			from api import Fault
			raise Fault(Fault.HOST_EXISTS, "host exists: %s" % host.name)
		HostStore.hosts[str(host.name)] = host
		if not HostStore.groups.has_key(host.group):
			HostStore.groups[host.group] = set()
		HostStore.groups[host.group].add(host)
		HostStore.save()
	add = static(add)
		
	def exists(host_name):
		"""
		Check whether a host exists
		@param host_name name of the host to find
		"""
		return HostStore.hosts.has_key(str(host_name))
	exists = static(exists)

	def group_exists(group_name):
		"""
		Check whether a host group exists
		@param group_name name of the group to find
		"""
		return HostStore.groups.has_key(str(group_name))
	group_exists = static(group_exists)

	def get(host_name):
		"""
		Retrieve a host by its name
		@param host_name name of the host to find
		"""
		if not HostStore.exists(host_name):
			from api import Fault
			raise Fault(Fault.NO_SUCH_HOST, "no such host: %s" % host_name)
		return HostStore.hosts[str(host_name)]
	get = static(get)
		
	def get_group(group_name):
		"""
		Retrieve all hosts of a group
		@param host_group name of the host group
		"""
		if not HostStore.group_exists(group_name):
			from api import Fault
			raise Fault(Fault.NO_SUCH_HOST_GROUP, "no such host group: %s" % group_name)
		return HostStore.groups[str(group_name)]
	get_group = static(get_group)

	def group_list():
		"""
		Retrieve all host groups
		"""
		return HostStore.groups.key_set()
	group_list = static(group_list)

	def remove(host_name):
		"""
		Remove a host from the host store
		@param host_name name of the host to remove
		"""
		if not HostStore.exists(host_name):
			from api import Fault
			raise Fault(Fault.NO_SUCH_HOST, "no such host: %s" % host_name)
		host = HostStore.hosts[host_name]
		del HostStore.hosts[host_name]
		HostStore.groups[host.group].remove(host)
		if HostStore.groups[host.group] == set():
			del HostStore.groups[host.group]
		HostStore.save()
	remove = static(remove)
	
	def update_host_usage():
		for host in HostStore.hosts.values():
			host.devices_total=0
			host.devices_started=0
		from topology_store import TopologyStore
		from topology import TopologyState
		for top in TopologyStore.topologies.values():
			for dev in top.devices.values():
				dev.host.devices_total = dev.host.devices_total + 1
				if top.state == TopologyState.STARTED:
					dev.host.devices_started = dev.host.devices_started + 1
	update_host_usage = static(update_host_usage)

	def select_host(group=None):
		best = None
		if group:
			hosts = HostStore.get_group(group)
		else:
			hosts = HostStore.hosts.values()
		for host in hosts:
			if not best:
				best = host
			if best.devices_total > host.devices_total or ( best.devices_total == host.devices_total and best.devices_started > host.devices_started ):
				best = host
		return best
	select_host = static(select_host)

HostStore.load()
atexit.register(HostStore.save)