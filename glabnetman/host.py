# -*- coding: utf-8 -*-

from resource_store import *
from util import *
from config import *

import subprocess

class Host(object):

	def __init__(self, name):
		self.name = name
		self.ports = ResourceStore(7000,1000)
		self.bridge_ids = ResourceStore(1000,1000)
		self.openvz_ids = ResourceStore(1000,100)
	
	def check(self):
		if parse_bool(Config.remote_dry_run):
			print "DRY RUN: ssh root@%s vzctl --version" % self.name
			print "DRY RUN: ssh root@%s brctl show" % self.name
			print "DRY RUN: ssh root@%s ipfw -h" % self.name
			print "DRY RUN: ssh root@%s tincd --version" % self.name
		else:
			print "checking for openvz..."
			subprocess.check_call (["ssh",  "root@%s" % self.name, "vzctl --version" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			print "checking for bridge utils..."
			subprocess.check_call (["ssh",  "root@%s" % self.name, "brctl show" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			print "checking for dummynet..."
			subprocess.check_call (["ssh",  "root@%s" % self.name, "ipfw -h" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			print "checking for tinc..."
			subprocess.check_call (["ssh",  "root@%s" % self.name, "tincd --version" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
