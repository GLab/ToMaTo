# -*- coding: utf-8 -*-

from django.db import models

import hosts, topology

class User():
	def __init__ (self, name, is_user, is_admin):
		self.name = name
		self.is_user = is_user
		self.is_admin = is_admin

class Device(models.Model):
	TYPE_OPENVZ="openvz"
	TYPE_KVM="kvm"
	TYPE_DHCPD="dhcpd"
	TYPES = ( (TYPE_OPENVZ, 'OpenVZ'), (TYPE_KVM, 'KVM'), (TYPE_DHCPD, 'DHCP server') )
	name = models.CharField(max_length=20)
	topology = models.ForeignKey(topology.Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	host = models.ForeignKey(hosts.Host)
	hostgroup = models.ForeignKey(hosts.HostGroup, null=True)

	def interfaces_get(self, name):
		return self.interface_set.get(name=name)

	def interfaces_add(self, iface):
		return self.interface_set.add(iface)

	def is_openvz(self):
		return type == Device.TYPE_OPENVZ

	def is_kvm(self):
		return type == Device.TYPE_KVM

	def is_dhcpd(self):
		return type == Device.TYPE_DHCPD

	def download_supported(self):
		return self.is_openvz() or self.is_kvm()
		
	def download_image(self, filename, task):
		if self.is_openvz():
			self.openvz.download_image(filename, task)
		if self.is_kvm():
			self.kvm.download_image(filename, task)
		
	def upload_supported(self):
		return self.is_openvz() or self.is_kvm()
		
	def upload_image(self, filename, task):
		if self.is_openvz():
			self.openvz.upload_image(filename, task)
		if self.is_kvm():
			self.kvm.upload_image(filename, task)
	
	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("id", self.name)
		dom.setAttribute("type", self.type)
		if self.hostgroup:
			dom.setAttribute("hostgroup", self.hostgroup)
		if internal:
			dom.setAttribute("host", self.host)
		for iface in self.interfaces:
			x_iface = doc.createElement ( "interface" )
			iface.encode_xml(x_iface, doc, internal)
			dom.appendChild(x_iface)
		if self.is_openvz():
			self.openvz.encode_xml(dom, doc, internal)
		if self.is_kvm():
			self.kvm.encode_xml(dom, doc, internal)
		if self.is_dhcpd():
			self.dhcpd.encode_xml(dom, doc, internal)
		
	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		self.type = dom.getAttribute("type")
		self.hostgroup = dom.getAttribute("hostgroup", None)
				
		
class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)
	
	def __init__(self, device, dom):
		self.device = device
		self.decode_xml(dom)
	
	def is_configured(self):
		#TODO
		return True
	
	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("id", self.name)
		if self.is_configured():
			self.configured_interface.encode_xml(dom, doc, internal)

	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")

class Connector(models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('real', 'Real network') )
	name = models.CharField(max_length=20)
	topology = models.ForeignKey(topology.Topology)
	type = models.CharField(max_length=10, choices=TYPES)

	def connections_add(self, con):
		return self.connection_set.add(con)

	def is_tinc(self):
		return type=='router' or type=='switch' or type=='hub'

	def is_internet(self):
		return type=='real'

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("name", self.name)
		dom.setAttribute("type", self.type)
		for con in self.connections:
			x_con = doc.createElement ( "connection" )
			con.encode_xml(x_con, doc, internal)
			dom.appendChild(x_con)
		if self.is_tinc():
			self.tinc.encode_xml(dom, doc, internal)
		if self.is_internet():
			self.internet.encode_xml(dom, doc, internal)

	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		self.type = dom.getAttribute("type")

class Connection(models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(Interface)
	bridge_id = models.IntegerField()
	bridge_special_name = models.CharField(max_length=15)

	def __init__ (self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)

	def is_emulated(self):
		#TODO
		return True

	def bridge_name(self):
		if self.bridge_special_name:
			return self.bridge_special_name
		return "gbr_" + self.bridge_id

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("device", self.interface.device.name)
		dom.setAttribute("interface", self.interface.name)
		if self.is_emulated():
			self.emulated.encode_xml(dom, doc, internal)

	def decode_xml(self, dom):
		device_name = dom.getAttribute("device")
		device = self.connector.topology.devices_get(device_name)
		iface_name = dom.getAttribute("interface")
		self.interface = device.interfaces_get(iface_name)
		
	def write_control_script(self, host, script, fd):
		"""
		Write the control scrips for this object and its child objects
		"""
		if script == "start":
			fd.write("brctl addbr %s\n" % self.bridge_name() )
			fd.write("ip link set %s up\n" % self.bridge_name() )
		if script == "stop":
			fd.write("ip link set %s down\n" % self.bridge_name() )
			fd.write("brctl delbr %s\n" % self.bridge_name() )