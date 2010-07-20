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
