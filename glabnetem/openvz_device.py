# -*- coding: utf-8 -*-

from device import *
from util import *

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

	def write_deploy_script(self, dir):
		id = self.id
		print "# deploying openvz %s ..." % self.id
		print "vzctl create %d --ostemplate debian" % id
		print "vzctl set %d --applyconfig virconel.basic --hostname myhost1  --devices c:10:200:rw  --capability net_admin:on --save" % id
		for iface in self.interfaces.values():
			print "vzctl set %d --netif_add %s,,,,br_%d_%s --save" % ( id, iface.id, id, iface.id )
			ip4 = iface.attributes.get("ip4_address",None)
			netmask = iface.attributes.get("ip4_netmask",None)
			if ip4:
				print "vzctl exec ifconfig %s %s %s up" % ( iface.id, ip4, netmask ) 
