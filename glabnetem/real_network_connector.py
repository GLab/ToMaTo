# -*- coding: utf-8 -*-

from connector import *
from util import *

class RealNetworkConnector(Connector):

	def __init__(self, topology, dom):
		Connector.__init__(self, topology, dom)
		if not self.physical_device:
			self.physical_device = "eth0"
	physical_device=property(curry(Connector.get_attr,"physical_device"),curry(Connector.set_attr,"physical_device"))

	def take_resources(self):
		pass

	def free_resources(self):
		pass

	def write_deploy_script(self):
		print "# deploying real network %s ..." % ( self.id )
		for con in self.connections:
			host = con.interface.device.host
			bridge_name=con.interface.device.bridge_name(con.interface)
			start_fd=open(self.topology.get_deploy_script(host.name,"start"), "a")
			start_fd.write ( "brctl addif %s %s\n" % (bridge_name, self.physical_device) )
			start_fd.close ()
			stop_fd=open(self.topology.get_deploy_script(host.name,"stop"), "a")
			stop_fd.write ( "brctl delif %s %s\n" % (bridge_name, self.physical_device) )
			stop_fd.close ()
