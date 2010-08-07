# -*- coding: utf-8 -*-

from device import *
from util import *

import config, api

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
	template=property(curry(Device.get_attr, "template", default=config.default_template), curry(Device.set_attr, "template"))
	root_password=property(curry(Device.get_attr, "root_password"), curry(Device.set_attr, "root_password"))
	
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
		Device.retake_resources(self)
		if self.openvz_id:
			self.host.openvz_ids.take_specific(self.openvz_id)
	
	def take_resources(self):
		"""
		Take free resources for all unassigned resource slots of thos object and its child objects. The number of the resources will be stored in internal fields.
		"""
		Device.take_resources(self)
		if not self.openvz_id:
			self.openvz_id=self.host.openvz_ids.take()

	def free_resources(self):
		"""
		Free all resources for all resource slots of this object and its child objects.
		"""
		Device.free_resources(self)
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

	def write_aux_files(self):
		"""
		Write the aux files for this object and its child objects
		"""
		pass

	def write_control_script(self, host, script, fd):
		"""
		Write the control script for this object and its child objects
		"""
		if script == "prepare":
			fd.write("vzctl create %s --ostemplate %s\n" % ( self.openvz_id, self.template ) )
			fd.write("vzctl set %s --devices c:10:200:rw  --capability net_admin:on --save\n" % self.openvz_id)
			if self.root_password:
				fd.write("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ) )
			if self.host_name:
				fd.write("vzctl set %s --hostname %s --save\n" % ( self.openvz_id, self.host_name ) )
			else:
				fd.write("vzctl set %s --hostname %s --save\n" % ( self.openvz_id, self.id ) )
			for iface in self.interfaces.values():
				bridge = self.bridge_name(iface)
				fd.write("vzctl set %s --netif_add %s --save\n" % ( self.openvz_id, iface.id ) )
				fd.write("vzctl set %s --ifname %s --host_ifname veth%s.%s --bridge %s --save\n" % ( self.openvz_id, iface.id, self.openvz_id, iface.id, bridge ) )
		if script == "destroy":
			fd.write("vzctl destroy %s\n" % self.openvz_id)
			fd.write ( "true\n" )
		if script == "start":
			for iface in self.interfaces.values():
				bridge = self.bridge_name(iface)
				fd.write("brctl addbr %s\n" % bridge )
				fd.write("ip link set %s up\n" % bridge )
			fd.write("vzctl start %s --wait\n" % self.openvz_id)
			for iface in self.interfaces.values():
				ip4 = iface.attributes.get("ip4_address",None)
				netmask = iface.attributes.get("ip4_netmask",None)
				dhcp = parse_bool(iface.attributes.get("use_dhcp",False))
				if ip4:
					fd.write("vzctl exec %s ifconfig %s %s netmask %s up\n" % ( self.openvz_id, iface.id, ip4, netmask ) ) 
				if dhcp:
					fd.write("vzctl exec %s \"[ -e /sbin/dhclient ] && /sbin/dhclient %s\"\n" % ( self.openvz_id, iface.id ) )
					fd.write("vzctl exec %s \"[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s\"\n" % ( self.openvz_id, iface.id ) )
		if script == "stop":
			fd.write("vzctl stop %s\n" % self.openvz_id)
			fd.write ( "true\n" )

	def check_change_possible(self, newdev):
		if not self.template == newdev.template:
			raise api.Fault(api.Fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Template of openvz vm %s cannot be changed" % self.id)
		if not self.host_name == newdev.host_name or not self.host_group == newdev.host_group:
			raise api.Fault(api.Fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Host of openvz vm %s cannot be changed" % self.id)

	def change(self, newdev, fd):
		"""
		Adapt this device to the new device
		"""
		self.root_password = newdev.root_password
		self.host_name = newdev.host_name
		self.host_group = newdev.host_group
		if self.root_password:
			fd.write("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ) )
		if self.host_name:
			fd.write("vzctl set %s --hostname %s --save\n" % ( self.openvz_id, self.host_name ) )
		else:
			fd.write("vzctl set %s --hostname %s --save\n" % ( self.openvz_id, self.id ) )
		for iface in self.interfaces.values():
			fd.write("vzctl set %s --netif_del %s --save\n" % ( self.openvz_id, iface.id ) )
		self.interfaces = newdev.interfaces
		for iface in self.interfaces.values():
			bridge = self.bridge_name(iface)
			fd.write("vzctl set %s --netif_add %s --save\n" % ( self.openvz_id, iface.id ) )
			fd.write("vzctl set %s --ifname %s --host_ifname veth%s.%s --bridge %s --save\n" % ( self.openvz_id, iface.id, self.openvz_id, iface.id, bridge ) )

	def __str__(self):
		return "openvz %s" % self.id
