# -*- coding: utf-8 -*-

from connector import *
from util import *

class RealNetworkConnector(Connector):
	"""
	This class represents a real network connector
	"""

	def __init__(self, topology, dom, load_ids):
		"""
		Creates a real network connector object
		@param topology the parent topology object
		@param dom the xml dom object of the connector
		@param load_ids whether to lod or ignore assigned ids
		"""
		Connector.__init__(self, topology, dom, load_ids)
		for con in self.connections:
			con.bridge_name = con.interface.device.host.public_bridge
			if con.delay or con.bandwidth or con.lossratio:
				raise Exception("ipfw not supported on real network")

	def retake_resources(self):
		"""
		Take all resources that this object and child objects once had. Fields containing the ids of assigned resources control which resources will be taken.
		"""
		pass

	def take_resources(self):
		"""
		Take free resources for all unassigned resource slots of thos object and its child objects. The number of the resources will be stored in internal fields.
		"""
		pass

	def free_resources(self):
		"""
		Free all resources for all resource slots of this object and its child objects.
		"""
		pass

	def write_aux_files(self):
		"""
		Write the aux files for this object and its child objects
		"""
		pass

	def write_control_script(self, host, script, fd):
		"""
		Write the control script for this object and its child objects
		"""
		# not invoking con.write_control_script()
		pass

	def __str__(self):
		return "real network %s" % self.id
