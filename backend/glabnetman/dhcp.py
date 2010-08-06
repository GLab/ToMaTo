# -*- coding: utf-8 -*-

from device import Device
from util import *

import os

class DhcpdDevice(Device):
	"""
	This class represents a dhcpd device 
	"""
  
	subnet=property(curry(Device.get_attr,"subnet"),curry(Device.set_attr,"subnet"))
	"""
	The subnet-number should be an IP address or domain name which resolves to the subnet number of the subnet being described. [dhcpd.conf.5]
	"""
	
	netmask=property(curry(Device.get_attr,"netmask"),curry(Device.set_attr,"netmask"))
	"""
	The  netmask  should  be  an  IP address or domain name which resolves to the subnet mask of the subnet being described. The subnet number, together with the netmask, are sufficient to determine whether any given IP address is on the specified subnet. [dhcpd.conf.5]
	"""
	range=property(curry(Device.get_attr,"range"),curry(Device.set_attr,"range"))
	"""
	Syntax: low-address [high-address]
	The range statement gives the lowest  and  highest IP addresses in a range. All IP addresses in the range should be in the subnet in which the range statement is declared. [...] When specifying a single address, high-address can be omitted. [dhcpd.conf.5]
	"""
	
	gateway=property(curry(Device.get_attr,"gateway"),curry(Device.set_attr,"gateway"))
	"""
	Syntax: ip-address [, ip-address...  ];
	The routers option specifies a list of IP addresses for routers on the client’s subnet. Routers should be listed in order of preference. [dhcp-options.5]
	"""
	
	nameserver=property(curry(Device.get_attr,"nameserver"),curry(Device.set_attr,"nameserver"))
	"""
	Syntax: ip-address [, ip-address...  ];
	The  domain-name-servers  option specifies a list of Domain Name System (STD 13, RFC 1035) name servers available to the client.  Servers should be listed in order of preference. [dhcp-options.5]
	"""

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

	def write_aux_files(self):
		"""
		Write the aux files for this object and its child objects
		"""
		dhcpd_fd=open(self.topology.get_control_dir(self.host_name)+"/dhcpd."+self.id+".conf","w")
		dhcpd_fd.write("subnet %s netmask %s {\n" % ( self.subnet, self.netmask ) )
		dhcpd_fd.write("  option routers %s;\n" % self.gateway )
		dhcpd_fd.write("  option domain-name-servers %s;\n" % self.nameserver )
		dhcpd_fd.write("  max-lease-time 300;\n" )
		dhcpd_fd.write("  range %s;\n" % self.range )
		dhcpd_fd.write("}\n" )

	def write_control_script(self, host, script, fd):
		"""
		Write the control script for this object and its child objects
		"""
		if script == "start":
			fd.write("dhcpd3 -cf dhcpd.%s.conf -pf %s.pid -lf leases" % ( self.id, self.id ) )
			for iface in self.interfaces.values():
				fd.write(" %s" % self.bridge_name(iface))
			fd.write(" &\n")
		if script == "stop":
			fd.write ( "cat %s.pid | xargs kill\n" % self.id )

	def check_change_possible(self, newdev):
		pass

	def change(self, newdev, fd):
		"""
		Adapt this device to the new device
		"""
		self.netmask=newdev.netmask
		self.range=newdev.range
		self.gateway=newdev.gateway
		self.nameserver=newdev.nameserver

	def __str__(self):
		return "dhcpd %s" % self.id
