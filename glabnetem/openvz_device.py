# -*- coding: utf-8 -*-

from device import *
from host_store import *
from util import *
from config import *

import os

class OpenVZDevice(Device):
  
	openvz_id=property(curry(Device.get_attr, "openvz_id"), curry(Device.set_attr, "openvz_id"))
	template=property(curry(Device.get_attr, "template", default=Config.default_template), curry(Device.set_attr, "template"))
	
	def take_resources(self):
		if not self.openvz_id:
			self.openvz_id=self.host.openvz_ids.take()

	def free_resources(self):
		if self.openvz_id:
			self.host.openvz_ids.free(self.openvz_id)
			self.openvz_id=None

	def bridge_name(self, interface):
		return "openvz_"+str(self.openvz_id)+"."+interface.id

	def write_deploy_script(self):
		create_fd=open(self.topology.get_deploy_script(self.host_name,"create"), "a")
		create_fd.write("vzctl create %s --ostemplate %s\n" % ( self.openvz_id, self.template ) )
		create_fd.write("vzctl set %s --devices c:10:200:rw  --capability net_admin:on --save\n" % self.openvz_id)
		destroy_fd=open(self.topology.get_deploy_script(self.host_name,"destroy"), "a")
		destroy_fd.write("vzctl destroy %s\n" % self.openvz_id)
		start_fd=open(self.topology.get_deploy_script(self.host_name,"start"), "a")
		start_fd.write("vzctl start --wait%s\n" % self.openvz_id)
		stop_fd=open(self.topology.get_deploy_script(self.host_name,"stop"), "a")
		stop_fd.write("vzctl stop %s\n" % self.openvz_id)
		for iface in self.interfaces.values():
			create_fd.write("vzctl set %s --netif_add %s,,,,%s --save\n" % ( self.openvz_id, iface.id, self.bridge_name(iface) ) )
			ip4 = iface.attributes.get("ip4_address",None)
			netmask = iface.attributes.get("ip4_netmask",None)
			if ip4:
				start_fd.write("vzctl exec ifconfig %s %s %s up\n" % ( iface.id, ip4, netmask ) ) 
		create_fd.close()
		destroy_fd.close()
		start_fd.close()
		stop_fd.close()
