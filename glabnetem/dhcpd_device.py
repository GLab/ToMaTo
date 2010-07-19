# -*- coding: utf-8 -*-

from device import *

class DhcpdDevice(Device):
  
	def __init__(self,topology,dom):
		Device.__init__(self,topology,dom)
		dhcpd = dom.getElementsByTagName("dhcpd-options")[0]
		self.subnet = dhcpd.getAttribute("subnet")
		self.netmask = dhcpd.getAttribute("netmask")
		self.range = dhcpd.getAttribute("range")
		self.gateway = dhcpd.getAttribute("gateway")
		self.nameserver = dhcpd.getAttribute("nameserver")
		
	def write_deploy_script(self, dir):
		print "# deploying dhcpd %s ..." % self.id
		print "# -------- dhcpd.conf -------------"
		print "subnet %s netmask %s {" % ( self.subnet, self.netmask )
		print "  option routers %s;" % self.gateway 
		print "  option domain-name-servers %s;" % self.nameserver
		print "  max-lease-time 300;"
		print "  range %s;" % self.range
		print "}"
		print "# ---------------------------------"
		print "brctl addbr br_%s_%s" % ( self.id, self.interfaces.values()[0].id )
		print "dhcpd -cf dhcpd.conf -lf leases br_%s_%s" % ( self.id, self.interfaces.values()[0].id )
