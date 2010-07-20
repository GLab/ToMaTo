# -*- coding: utf-8 -*-

from util import *

class HostStore(object):

	hosts = {}
		
	def add(host):
		HostStore.hosts[host.name] = host
	add = static(add)
		
	def get(host_name):
		return HostStore.hosts[host_name]
	get = static(get)
		
	def remove(host_name):
		del HostStore.hosts[host_name]
	remove = static(remove)
