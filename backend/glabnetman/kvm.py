# -*- coding: utf-8 -*-

from django.db import models

import generic

class KVMDevice(generic.Device):
	kvm_id = models.IntegerField()
	template = models.CharField(max_length=30)
	
	def __init__(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = generic.Interface(self, interface)
			self.interfaces_add(iface)
	
	def download_image(self, filename, task):
		pass

	def upload_image(self, filename, task):
		pass

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("template", self.template)
		if internal:
			dom.setAttribute("kvm_id", self.kvm_id)
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")
