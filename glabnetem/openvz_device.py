# -*- coding: utf-8 -*-

from device import *
from host_store import *
from util import *
from config import *

import os

class OpenVZDevice(Device):
  
	openvz_id=property(curry(Device.get_attr, "openvz_id"), curry(Device.set_attr, "openvz_id"))
	template=property(curry(Device.get_attr, "template", default=Config.default_template), curry(Device.set_attr, "template"))
	
	def retake_resources(self):
		if self.openvz_id:
			self.host.openvz_ids.take_specific(self.openvz_id)
	
	def take_resources(self):
		if not self.openvz_id:
			self.openvz_id=self.host.openvz_ids.take()

	def free_resources(self):
		if self.openvz_id:
			self.host.openvz_ids.free(self.openvz_id)
			self.openvz_id=None

	def bridge_name(self, interface):
		# must be 16 chars or less
		if interface.connection:
			return interface.connection.bridge_name
		else:
			return None

	def write_deploy_script(self):
		print "\tcreating scripts for openvz %s ..." % self.id
		create_fd=open(self.topology.get_deploy_script(self.host_name,"create"), "a")
		create_fd.write("vzctl create %s --ostemplate %s\n" % ( self.openvz_id, self.template ) )
		create_fd.write("vzctl set %s --devices c:10:200:rw  --capability net_admin:on --save\n" % self.openvz_id)
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
			stop_fd.write("ip link set %s down\n" % bridge )
			stop_fd.write("brctl delbr %s\n" % bridge )
		start_fd.write("vzctl start %s --wait\n" % self.openvz_id)
		for iface in self.interfaces.values():
			ip4 = iface.attributes.get("ip4_address",None)
			netmask = iface.attributes.get("ip4_netmask",None)
			if ip4:
				start_fd.write("vzctl exec %s ifconfig %s %s netmask %s up\n" % ( self.openvz_id, iface.id, ip4, netmask ) ) 
		create_fd.close()
		destroy_fd.write ( "true\n" )
		destroy_fd.close()
		start_fd.close()
		stop_fd.write ( "true\n" )
		stop_fd.close()
