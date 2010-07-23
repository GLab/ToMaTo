# -*- coding: utf-8 -*-

from device import *
from host_store import *
from util import *
from config import *

import os

class OpenVZDevice(Device):
	"""
	This class represents an openvz device
	"""

	def __init__(self, topology, dom, load_ids):
		"""
		Creates an openvz device object
		@param topology the parent topology object
		@param dom the xml dom object of the device
		@param load_ids whether to lod or ignore assigned ids
		"""
		Device.__init__(self, topology, dom, load_ids)
		self.decode_xml(dom, load_ids)

	openvz_id=property(curry(Device.get_attr, "openvz_id"), curry(Device.set_attr, "openvz_id"))
	template=property(curry(Device.get_attr, "template", default=Config.default_template), curry(Device.set_attr, "template"))
	root_password=property(curry(Device.get_attr, "root_password"), curry(Device.set_attr, "root_password"))
	hostname=property(curry(Device.get_attr, "hostname"), curry(Device.set_attr, "hostname"))
	
	def decode_xml ( self, dom, load_ids ):
		"""
		Read the attributes from the xml dom object
		@param dom the xml dom object to read the data from
		@load_ids whether to load or ignore assigned ids
		"""
		if not load_ids:
			if dom.hasAttribute("openvz_id"):
				dom.removeAttribute("openvz_id")

	def encode_xml ( self, dom, doc, print_ids ):
		"""
		Encode the object to an xml dom object
		@param dom the xml dom object to write the data to
		@param doc the xml document needed to create child elements
		@print_ids whether to include or ignore assigned ids
		"""
		Device.encode_xml(self,dom,doc,print_ids)
		if not print_ids:
			if dom.hasAttribute("openvz_id"):
				dom.removeAttribute("openvz_id")

	def retake_resources(self):
		"""
		Take all resources that this object and child objects once had. Fields containing the ids of assigned resources control which resources will be taken.
		"""
		if self.openvz_id:
			self.host.openvz_ids.take_specific(self.openvz_id)
	
	def take_resources(self):
		"""
		Take free resources for all unassigned resource slots of thos object and its child objects. The number of the resources will be stored in internal fields.
		"""
		if not self.openvz_id:
			self.openvz_id=self.host.openvz_ids.take()

	def free_resources(self):
		"""
		Free all resources for all resource slots of this object and its child objects.
		"""
		if self.openvz_id:
			self.host.openvz_ids.free(self.openvz_id)
			self.openvz_id=None

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
		print "\tcreating scripts for openvz %s ..." % self.id
		create_fd=open(self.topology.get_deploy_script(self.host_name,"create"), "a")
		create_fd.write("vzctl create %s --ostemplate %s\n" % ( self.openvz_id, self.template ) )
		create_fd.write("vzctl set %s --devices c:10:200:rw  --capability net_admin:on --save\n" % self.openvz_id)
		if self.root_password:
			create_fd.write("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ) )
		if self.hostname:
			create_fd.write("vzctl set %s --hostname %s --save\n" % ( self.openvz_id, self.hostname ) )
		else:
			create_fd.write("vzctl set %s --hostname %s --save\n" % ( self.openvz_id, self.id ) )

		destroy_fd=open(self.topology.get_deploy_script(self.host_name,"destroy"), "a")
		destroy_fd.write("vzctl destroy %s\n" % self.openvz_id)
		stop_fd=open(self.topology.get_deploy_script(self.host_name,"stop"), "a")
		stop_fd.write("vzctl stop %s\n" % self.openvz_id)
		start_fd=open(self.topology.get_deploy_script(self.host_name,"start"), "a")
		for iface in self.interfaces.values():
			bridge = self.bridge_name(iface)
			create_fd.write("vzctl set %s --netif_add %s --save\n" % ( self.openvz_id, iface.id ) )
			create_fd.write("vzctl set %s --ifname %s --host_ifname veth%s.%s --bridge %s --save\n" % ( self.openvz_id, iface.id, self.openvz_id, iface.id, bridge ) )
			start_fd.write("brctl addbr %s\n" % bridge )
			start_fd.write("ip link set %s up\n" % bridge )
		start_fd.write("vzctl start %s --wait\n" % self.openvz_id)
		for iface in self.interfaces.values():
			ip4 = iface.attributes.get("ip4_address",None)
			netmask = iface.attributes.get("ip4_netmask",None)
			dhcp = parse_bool(iface.attributes.get("use_dhcp",False))
			if ip4:
				start_fd.write("vzctl exec %s ifconfig %s %s netmask %s up\n" % ( self.openvz_id, iface.id, ip4, netmask ) ) 
			if dhcp:
				start_fd.write("vzctl exec %s \"[ -e /sbin/dhclient ] && /sbin/dhclient %s\"\n" % ( self.openvz_id, iface.id ) )
				start_fd.write("vzctl exec %s \"[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s\"\n" % ( self.openvz_id, iface.id ) )
		create_fd.close()
		destroy_fd.write ( "true\n" )
		destroy_fd.close()
		start_fd.close()
		stop_fd.write ( "true\n" )
		stop_fd.close()
