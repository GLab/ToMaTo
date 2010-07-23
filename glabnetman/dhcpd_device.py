# -*- coding: utf-8 -*-

from device import *
from util import *

import os

class DhcpdDevice(Device):
	"""
	This class represents a dhcpd device 
	"""
  
	subnet=property(curry(Device.get_attr,"subnet"),curry(Device.set_attr,"subnet"))
	netmask=property(curry(Device.get_attr,"netmask"),curry(Device.set_attr,"netmask"))
	range=property(curry(Device.get_attr,"range"),curry(Device.set_attr,"range"))
	gateway=property(curry(Device.get_attr,"gateway"),curry(Device.set_attr,"gateway"))
	nameserver=property(curry(Device.get_attr,"nameserver"),curry(Device.set_attr,"nameserver"))

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

	def bridge_name(self, interface):
		"""
		Returns the name of the bridge for the connection of the given interface
		Note: This must be 16 characters or less for brctl to work
		@param interface the interface
		"""
		if interface.connection:
			return interface.connection.bridge_name
		else:
			return None

	def write_deploy_script(self):
		"""
		Write the control scrips for this object and its child objects
		"""
		print "\tcreating scripts for dhcpd %s ..." % self.id
		dhcpd_fd=open(self.topology.get_deploy_dir(self.host_name)+"/dhcpd."+self.id+".conf","w")
		dhcpd_fd.write("subnet %s netmask %s {\n" % ( self.subnet, self.netmask ) )
		dhcpd_fd.write("  option routers %s;\n" % self.gateway )
		dhcpd_fd.write("  option domain-name-servers %s;\n" % self.nameserver )
		dhcpd_fd.write("  max-lease-time 300;\n" )
		dhcpd_fd.write("  range %s;\n" % self.range )
		dhcpd_fd.write("}\n" )
		start_fd=open(self.topology.get_deploy_script(self.host_name,"start"), "a")
		start_fd.write("dhcpd -cf dhcpd.%s.conf -pf %s.pid -lf leases" % ( self.id, self.id ) )
		for iface in self.interfaces.values():
			start_fd.write(" %s" % self.bridge_name(iface))
		start_fd.write(" &\n")
		start_fd.close()
		stop_fd=open(self.topology.get_deploy_script(self.host_name,"stop"), "a")
		stop_fd.write ( "cat %s.pid | xargs kill\n" % self.id )
		stop_fd.close()
