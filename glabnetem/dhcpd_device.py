# -*- coding: utf-8 -*-

from device import *
from util import *

import os

class DhcpdDevice(Device):
  
	subnet=property(curry(Device.get_attr,"subnet"),curry(Device.set_attr,"subnet"))
	netmask=property(curry(Device.get_attr,"netmask"),curry(Device.set_attr,"netmask"))
	range=property(curry(Device.get_attr,"range"),curry(Device.set_attr,"range"))
	gateway=property(curry(Device.get_attr,"gateway"),curry(Device.set_attr,"gateway"))
	nameserver=property(curry(Device.get_attr,"nameserver"),curry(Device.set_attr,"nameserver"))

	def take_resources(self):
		pass

	def free_resources(self):
		pass

	def bridge_name(self, interface):
		return "dhcpd_"+self.id+"."+interface.id

	def write_deploy_script(self):
		print "\tcreating scripts for dhcpd %s ..." % self.id
		dhcpd_fd=open(self.topology.get_deploy_dir(self.host_name)+"/dhcpd."+self.id+".conf","w")
		dhcpd_fd.write("subnet %s netmask %s {\n" % ( self.subnet, self.netmask ) )
		dhcpd_fd.write("  option routers %s;\n" % self.gateway )
		dhcpd_fd.write("  option domain-name-servers %s;\n" % self.nameserver )
		dhcpd_fd.write("  max-lease-time 300;\n" )
		dhcpd_fd.write("  range %s;\n" % self.range )
		dhcpd_fd.write("}\n" )
		start_fd=open(self.topology.get_deploy_script(self.host_name,"start"), "a")
		for iface in self.interfaces.values():
			start_fd.write("brctl addbr %s\n" % self.bridge_name(iface) )
		start_fd.write("dhcpd -cf dhcpd.%s.conf -pf %s.pid -lf leases" % ( self.id, self.id ) )
		for iface in self.interfaces.values():
			start_fd.write(" %s" % self.bridge_name(iface))
		start_fd.write(" &\n")
		start_fd.close()
		stop_fd=open(self.topology.get_deploy_script(self.host_name,"stop"), "a")
		for iface in self.interfaces.values():
			stop_fd.write("brctl delbr %s\n" % self.bridge_name(iface) )
		stop_fd.write ( "cat %s.pid | xargs kill\n" % self.id )
		stop_fd.close()
