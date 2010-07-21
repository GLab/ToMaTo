# -*- coding: utf-8 -*-

from connector import *
from util import *

class RealNetworkConnector(Connector):

	def __init__(self, topology, dom):
		Connector.__init__(self, topology, dom)
		if not self.bridge_name:
			self.bridge_name = "vmbr0"
	bridge_name=property(curry(Connector.get_attr,"bridge_name"),curry(Connector.set_attr,"bridge_name"))

	def take_resources(self):
		pass

	def free_resources(self):
		pass

	def write_deploy_script(self):
		print "\tcreating scripts for real network %s ..." % ( self.id )
		for con in self.connections:
			host = con.interface.device.host
			bridge_name=con.interface.device.bridge_name(con.interface)
			start_fd=open(self.topology.get_deploy_script(host.name,"start"), "a")
			#start_fd.write ( "brctl addif %s %s\n" % (bridge_name, self.physical_device) )
			#FIXME not working
			start_fd.close ()
			stop_fd=open(self.topology.get_deploy_script(host.name,"stop"), "a")
			#stop_fd.write ( "brctl delif %s %s\n" % (bridge_name, self.physical_device) )
			#FIXME not working
			stop_fd.close ()
