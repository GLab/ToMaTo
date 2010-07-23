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
		if not self.bridge_name:
			self.bridge_name = "vmbr0"
		for con in self.connections:
			con.bridge_name = self.bridge_name
			if con.delay or con.bandwidth or con.lossratio:
				raise Exception("ipfw not supported on real network")

	bridge_name=property(curry(Connector.get_attr,"bridge_name"),curry(Connector.set_attr,"bridge_name"))

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

	def write_deploy_script(self):
		"""
		Write the control scrips for this object and its child objects
		"""
		print "\tcreating scripts for real network %s ..." % ( self.id )
		# not invoking con.write_deploy_script()
		for con in self.connections:
			host = con.interface.device.host
			bridge_name=con.bridge_name
			start_fd=open(self.topology.get_deploy_script(host.name,"start"), "a")
			start_fd.close ()
			stop_fd=open(self.topology.get_deploy_script(host.name,"stop"), "a")
			stop_fd.close ()
