# -*- coding: utf-8 -*-

from util import XmlObject, curry, run_shell

import config, resource

class Host(XmlObject):
	"""
	This class represents a host
	"""

	name=property(curry(XmlObject.get_attr, "name"), curry(XmlObject.set_attr, "name"))
	group=property(curry(XmlObject.get_attr, "group"), curry(XmlObject.set_attr, "group"))
	public_bridge=property(curry(XmlObject.get_attr, "public_bridge"), curry(XmlObject.set_attr, "public_bridge"))

	def __init__(self):
		"""
		Creates a new host object
		"""
		self.attributes={}
		self.devices=set()
		self.ports = resource.Store(7000,1000)
		self.bridge_ids = resource.Store(1000,1000)
		self.openvz_ids = resource.Store(1000,100)
		
	def decode_xml(self,dom):
		XmlObject.decode_xml(self,dom)
		if not self.public_bridge:
			self.public_bridge = "vmbr0"

	def check(self, task):
		"""
		Checks if the host is reachable, login works and the needed software is installed
		"""
		task.output.write("checking for openvz...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "vzctl --version" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write("checking for bridge utils...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "brctl show" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write("checking for dummynet...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "ipfw -h" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write("checking for tinc...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "tincd --version" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
