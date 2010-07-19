# -*- coding: utf-8 -*-

from device import *

import os

class DhcpdDevice(Device):
  
	def __init__(self,topology,dom):
		Device.__init__(self,topology,dom)
		dhcpd = dom.getElementsByTagName("dhcpd-options")[0]
		self.subnet = dhcpd.getAttribute("subnet")
		self.netmask = dhcpd.getAttribute("netmask")
		self.range = dhcpd.getAttribute("range")
		self.gateway = dhcpd.getAttribute("gateway")
		self.nameserver = dhcpd.getAttribute("nameserver")

	def take_resources(self):
		pass

	def free_resources(self):
		pass

	def bridge_name(self, interface):
		return "dhcpd_"+self.id+"."+interface.id

	def write_deploy_script(self, dir):
		print "# deploying dhcpd %s ..." % self.id
		if not os.path.exists(dir+"/"+self.host):
			os.makedirs(dir+"/"+self.host)
		dhcpd_fd=open(dir+"/"+self.host+"/dhcpd."+self.id+".conf","w")
		dhcpd_fd.write("subnet %s netmask %s {\n" % ( self.subnet, self.netmask ) )
		dhcpd_fd.write("  option routers %s;\n" % self.gateway )
		dhcpd_fd.write("  option domain-name-servers %s;\n" % self.nameserver )
		dhcpd_fd.write("  max-lease-time 300;\n" )
		dhcpd_fd.write("  range %s;\n" % self.range )
		dhcpd_fd.write("}\n" )
		startup_fd=open(dir+"/%s/startup.sh" % self.host, "a")
		startup_fd.write("brctl addbr %s\n" % self.bridge_name(self.interfaces.values()[0]) )
		startup_fd.write("dhcpd -cf dhcpd.%s.conf -lf leases %s\n" % ( self.id, self.bridge_name(self.interfaces.values()[0]) ) )
		startup_fd.close()
