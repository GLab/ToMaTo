# -*- coding: utf-8 -*-

from resource_store import *

class Host(object):

	def __init__(self, name):
		self.name = name
		self.ports = ResourceStore(7000,10)
		self.bridge_ids = ResourceStore(1000,10)
		self.openvz_ids = ResourceStore(1000,10)