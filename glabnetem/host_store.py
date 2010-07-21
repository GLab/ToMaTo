# -*- coding: utf-8 -*-

from util import *
from config import *
from host import *

from xml.dom import minidom
import atexit, os

class HostStore(object):
		
	hosts = {}
	
	def load ():
		if not os.path.exists ( Config.hosts ):
			return
		dom = minidom.parse ( Config.hosts )
		x_hosts = dom.getElementsByTagName ( "hosts" )[0]
		for x_host in x_hosts.getElementsByTagName ( "host" ):
			HostStore.add ( Host ( x_host.getAttribute("name") ) )
	load = static(load)
			
	def save ():
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
		HostStore.hosts[str(host.name)] = host
	add = static(add)
		
	def get(host_name):
		return HostStore.hosts[str(host_name)]
	get = static(get)
		
	def remove(host_name):
		del HostStore.hosts[str(host_name)]
	remove = static(remove)

HostStore.load()
atexit.register(HostStore.save)
