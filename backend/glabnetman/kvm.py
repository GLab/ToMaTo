# -*- coding: utf-8 -*-

from django.db import models

import generic, hosts

def next_free_id (host):
	ids = range(1000,1100)
	for dev in KVMDevice.objects.filter(host=host):
		ids.remove(dev.kvm_id)
	return ids[0]

class KVMDevice(generic.Device):
	kvm_id = models.IntegerField()
	template = models.CharField(max_length=30)
	
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.host = hosts.get_best_host(self.hostgroup)
		self.kvm_id = next_free_id(self.host)
		self.save()		
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = generic.Interface()
			iface.init(self, interface)
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

	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass
