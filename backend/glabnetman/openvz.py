# -*- coding: utf-8 -*-

from django.db import models

import generic

class OpenVZDevice(generic.Device):
	openvz_id = models.IntegerField()
	root_password = models.CharField(max_length=50, null=True)
	template = models.CharField(max_length=30)
	
	def __init__(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = ConfiguredInterface(self, interface)
			self.interfaces_add(iface)
	
	def download_image(self, filename, task):
		pass

	def upload_image(self, filename, task):
		pass

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("template", self.template)
		if self.root_password:
			dom.setAttribute("root_password", self.root_password)
		if internal:
			dom.setAttribute("openvz_id", self.openvz_id)
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")
		self.root_password = dom.getAttribute("root_password")


class ConfiguredInterface(generic.Interface):
	use_dhcp = models.NullBooleanField()
	ip4address = models.CharField(max_length=15, null=True)
	ip4netmask = models.CharField(max_length=15, null=True)

	def __init__(self, device, dom):
		self.device = device
		self.decode_xml(dom)

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("use_dhcp", self.use_dhcp)
		if self.ip4address:
			dom.setAttribute("ip4address", self.ip4address)
		if self.ip4netmask:
			dom.setAttribute("ip4netmask", self.ip4netmask)
		
	def decode_xml(self, dom):
		generic.Interface.decode_xml(self, dom)
		self.use_dhcp = dom.getAttribute("use_dhcp")
		self.ip4address = dom.getAttribute("ip4address", None)
		self.ip4netmask = dom.getAttribute("ip4netmask", None)