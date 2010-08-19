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

	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Device.encode_xml(self, dom, doc, internal)
		dom.setAttribute("subnet", self.subnet)
		dom.setAttribute("netmask", self.netmask)
		dom.setAttribute("range", self.range)
		dom.setAttribute("gateway", self.gateway)
		dom.setAttribute("nameserver", self.nameserver)
		
	def decode_xml(self, dom, recurse=True):
		if recurse:
			generic.Device.decode_xml(self, dom)
		self.subnet = dom.getAttribute("subnet")
		self.netmask = dom.getAttribute("netmask")
		self.range = dom.getAttribute("range")
		self.gateway = dom.getAttribute("gateway")
		self.nameserver = dom.getAttribute("nameserver")

	def start(self, task):
		generic.Device.start(self, task)
		command = "dhcpd3 -cf dhcpd.%s.conf -pf %s.pid -lf leases" % ( self.name, self.name )
		for iface in self.interfaces_all():
			command += " %s" % self.bridge_name(iface)
		command += " &"
		self.host.execute(command, task)

	def stop(self, task):
		generic.Device.stop(self, task)
		self.host.execute("cat %s.pid | xargs kill\n" % self.name, task)

	def prepare(self, task):
		generic.Device.prepare(self, task)
		local_file = self.topology.get_control_dir(self.host_name)+"/dhcpd."+self.name+".conf"
		dhcpd_fd=open(local_file,"w")
		dhcpd_fd.write("subnet %s netmask %s {\n" % ( self.subnet, self.netmask ) )
		dhcpd_fd.write("  option routers %s;\n" % self.gateway )
		dhcpd_fd.write("  option domain-name-servers %s;\n" % self.nameserver )
		dhcpd_fd.write("  max-lease-time 300;\n" )
		dhcpd_fd.write("  range %s;\n" % self.range )
		dhcpd_fd.write("}\n" )
		self.host.upload(local_file, self.topology.get_remote_control_dir()+"/dhcpd."+self.name+".conf", task)

	def destroy(self, task):
		generic.Device.destroy(self, task)
		self.host.execute("rm " + self.topology.get_remote_control_dir()+"/dhcpd."+self.name+".conf", task)

	def change_possible(self, dom):
		generic.Device.change_possible(self, dom)

	def change_run(self, dom, task):
		"""
		Adapt this device to the new device
		"""
		self.decode_xml(dom, False)
		if self.topology.state == "prepared" or self.topology.state == "started":
			self.prepare(task)
		if self.topology.state == "started":
			self.stop(task)
			self.start(task)
