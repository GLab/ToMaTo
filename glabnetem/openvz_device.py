# -*- coding: utf-8 -*-

from device import *
from util import *

import os

class OpenVZDevice(Device):
  
	openvz_ids = {}
	
	def set_openvz_ids(host, res):
		OpenVZDevice.openvz_ids[host] = res
	set_openvz_ids = Callable(set_openvz_ids)
	
	def get_openvz_ids(host):
		return OpenVZDevice.openvz_ids[host]
	get_openvz_ids = Callable(get_openvz_ids)
	
	def take_resources(self):
		if not self.id:
			self.id = OpenVZDevice.openvz_ids[self.host].take()

	def free_resources(self):
		if self.id:
			OpenVZDevice.openvz_ids[self.host].free(self.id)
			self.id = None

	def bridge_name(self, interface):
		return "openvz_"+self.id+"."+interface.id

	def write_deploy_script(self, dir):
		print "# deploying openvz %s ..." % self.id
		if not os.path.exists(dir+"/"+self.host):
			os.makedirs(dir+"/"+self.host)
		startup_fd=open(dir+"/%s/startup.sh" % self.host, "a")
		startup_fd.write("vzctl create %s --ostemplate debian\n" % self.id)
		startup_fd.write("vzctl set %s --applyconfig virconel.basic --hostname myhost1  --devices c:10:200:rw  --capability net_admin:on --save\n" % self.id)
		for iface in self.interfaces.values():
			startup_fd.write("vzctl set %s --netif_add %s,,,,%s --save\n" % ( self.id, iface.id, self.bridge_name(iface) ) )
			ip4 = iface.attributes.get("ip4_address",None)
			netmask = iface.attributes.get("ip4_netmask",None)
			if ip4:
				startup_fd.write("vzctl exec ifconfig %s %s %s up\n" % ( iface.id, ip4, netmask ) ) 
		startup_fd.close()
