# -*- coding: utf-8 -*-

from util import *
from config import *
from host import *

from xml.dom import minidom
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
	
	def load ():
		"""
		Load hosts from file
		"""
		if not os.path.exists ( Config.hosts ):
			return
		dom = minidom.parse ( Config.hosts )
		x_hosts = dom.getElementsByTagName ( "hosts" )[0]
		for x_host in x_hosts.getElementsByTagName ( "host" ):
			HostStore.add ( Host ( x_host.getAttribute("name") ) )
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
			x_host.setAttribute("name", host.name)
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
		HostStore.hosts[str(host.name)] = host
		HostStore.save()
	add = static(add)
		
	def get(host_name):
		"""
		Retrieve a host by its name
		@param host_name name of the host to find
		"""
		return HostStore.hosts[str(host_name)]
	get = static(get)
		
	def remove(host_name):
		"""
		Remove a host from the host store
		@param host_name name of the host to remove
		"""
		del HostStore.hosts[str(host_name)]
		HostStore.save()
	remove = static(remove)

HostStore.load()
atexit.register(HostStore.save)
