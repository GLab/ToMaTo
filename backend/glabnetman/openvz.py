# -*- coding: utf-8 -*-

from django.db import models

import generic, util, hosts, hashlib, config

def next_free_id (host):
	ids = range(1000,1100)
	for dev in OpenVZDevice.objects.filter(host=host):
		ids.remove(dev.openvz_id)
	return ids[0]

class OpenVZDevice(generic.Device):
	openvz_id = models.IntegerField()
	root_password = models.CharField(max_length=50, null=True)
	template = models.CharField(max_length=30)
	vnc_port = models.IntegerField()
		
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.host = hosts.get_best_host(self.hostgroup)
		self.openvz_id = next_free_id(self.host)
		self.vnc_port = hosts.next_free_port(self.host)
		self.save()
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = ConfiguredInterface()
			iface.init(self, interface)
			self.interfaces_add(iface)
	
	def vnc_password(self):
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.id))
		m.update(str(self.openvz_id))
		m.update(str(self.vnc_port))
		m.update(str(self.topology.owner))
		return m.hexdigest()
	
	def download_image(self, filename, task):
		pass

	def upload_image(self, filename, task):
		pass

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("template", self.template)
		if self.root_password:
			dom.setAttribute("root_password", self.root_password)
		if internal:
			dom.setAttribute("openvz_id", str(self.openvz_id))
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")
		self.root_password = dom.getAttribute("root_password")

	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass


class ConfiguredInterface(generic.Interface):
	use_dhcp = models.BooleanField()
	ip4address = models.CharField(max_length=15, null=True)
	ip4netmask = models.CharField(max_length=15, null=True)

	def init(self, device, dom):
		self.device = device
		self.decode_xml(dom)
		self.save()

	def encode_xml(self, dom, doc, internal):
		if self.use_dhcp:
			dom.setAttribute("use_dhcp", str(self.use_dhcp).lower())
		if self.ip4address:
			dom.setAttribute("ip4address", self.ip4address)
		if self.ip4netmask:
			dom.setAttribute("ip4netmask", self.ip4netmask)
		
	def decode_xml(self, dom):
		generic.Interface.decode_xml(self, dom)
		self.use_dhcp = util.parse_bool(util.get_attr(dom, "use_dhcp", default="false"))
		self.ip4address = util.get_attr(dom, "ip4address", default=None)
		self.ip4netmask = util.get_attr(dom, "ip4netmask", default=None)
		
	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass	