# -*- coding: utf-8 -*-

from django.db import models

import generic, hosts

class DhcpdDevice(generic.Device):
	subnet = models.CharField(max_length=15)
	netmask = models.CharField(max_length=15)
	range = models.CharField(max_length=31)
	gateway = models.CharField(max_length=15)
	nameserver = models.CharField(max_length=15)

	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.host = hosts.get_best_host(self.hostgroup)
		self.save()
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = generic.Interface()
			iface.init(self, interface)
			self.interfaces_add(iface)

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("subnet", self.subnet)
		dom.setAttribute("netmask", self.netmask)
		dom.setAttribute("range", self.range)
		dom.setAttribute("gateway", self.gateway)
		dom.setAttribute("nameserver", self.nameserver)
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.subnet = dom.getAttribute("subnet")
		self.netmask = dom.getAttribute("netmask")
		self.range = dom.getAttribute("range")
		self.gateway = dom.getAttribute("gateway")
		self.nameserver = dom.getAttribute("nameserver")
		
	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass
