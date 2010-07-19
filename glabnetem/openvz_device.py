# -*- coding: utf-8 -*-

from device import *

class OpenVZDevice(Device):
  
	def deploy(self, dir):
		print "# deploying openvz %s ..." % self.id
		id = int(self.topology.id)+1000
		print "vzctl create %d --ostemplate debian" % id
		print "vzctl set %d --applyconfig virconel.basic --hostname myhost1  --devices c:10:200:rw  --capability net_admin:on --save" % id
		for iface in self.interfaces.values():
			print "vzctl set %d --netif_add %s,,,,br_%d_%s --save" % ( id, iface.id, id, iface.id )
			ip4 = iface.attributes.get("ip4_address",None)
			netmask = iface.attributes.get("ip4_netmask",None)
			if ip4:
				print "vzctl exec ifconfig %s %s %s up" % ( iface.id, ip4, netmask ) 
