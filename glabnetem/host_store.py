# -*- coding: utf-8 -*-

from util import *
from config import *

import shelve, atexit

class HostStore(object):
		
	def load():
		HostStore.hosts=shelve.open(Config.hosts_shelve,writeback=True)
	load = static(load)
		
	def save():
		HostStore.hosts.sync()
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
