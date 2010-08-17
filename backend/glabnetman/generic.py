# -*- coding: utf-8 -*-

from django.db import models

import hosts, util

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
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	host = models.ForeignKey(hosts.Host)
	hostgroup = models.ForeignKey(hosts.HostGroup, null=True)

	def interfaces_get(self, name):
		return self.interface_set.get(name=name)

	def interfaces_add(self, iface):
		return self.interface_set.add(iface)

	def interfaces_all(self):
		return self.interface_set.all()

	def is_openvz(self):
		return self.type == Device.TYPE_OPENVZ

	def is_kvm(self):
		return self.type == Device.TYPE_KVM

	def is_dhcpd(self):
		return self.type == Device.TYPE_DHCPD

	def download_supported(self):
		return self.is_openvz() or self.is_kvm()
		
	def download_image(self, filename, task):
		if self.is_openvz():
			self.openvzdevice.download_image(filename, task)
		if self.is_kvm():
			self.kvmdevice.download_image(filename, task)
		
	def upload_supported(self):
		return self.is_openvz() or self.is_kvm()
		
	def upload_image(self, filename, task):
		if self.is_openvz():
			self.openvzdevice.upload_image(filename, task)
		if self.is_kvm():
			self.kvmdevice.upload_image(filename, task)
	
	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("id", self.name)
		dom.setAttribute("type", self.type)
		if self.hostgroup:
			dom.setAttribute("hostgroup", self.hostgroup)
		if internal:
			dom.setAttribute("host", self.host)
		for iface in self.interfaces_all():
			x_iface = doc.createElement ( "interface" )
			iface.encode_xml(x_iface, doc, internal)
			dom.appendChild(x_iface)
		if self.is_openvz():
			self.openvzdevice.encode_xml(dom, doc, internal)
		if self.is_kvm():
			self.kvmdevice.encode_xml(dom, doc, internal)
		if self.is_dhcpd():
			self.dhcpddevice.encode_xml(dom, doc, internal)
		
	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		self.type = dom.getAttribute("type")
		util.get_attr(dom, "hostgroup", default=None)
		
	def write_aux_files(self):
		if self.is_openvz():
			self.openvzdevice.write_aux_files()
		if self.is_kvm():
			self.kvmdevice.write_aux_files()
		if self.is_dhcpd():
			self.dhcpddevice.write_aux_files()
	
	def write_control_script(self, host, script, fd):
		if self.is_openvz():
			self.openvzdevice.write_control_script(host, script, fd)
		if self.is_kvm():
			self.kvmdevice.write_control_script(host, script, fd)
		if self.is_dhcpd():
			self.dhcpddevice.write_control_script(host, script, fd)

	def __unicode__(self):
		return self.name
		
		
class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)
	
	def init(self, device, dom):
		self.device = device
		self.decode_xml(dom)
		self.save()
	
	def is_configured(self):
		try:
			self.configuredinterface
			return True
		except:
			return False
	
	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("id", self.name)
		if self.is_configured():
			self.configuredinterface.encode_xml(dom, doc, internal)

	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		
	def __unicode__(self):
		return str(self.device.name)+"."+str(self.name)
		

class Connector(models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('real', 'Real network') )
	name = models.CharField(max_length=20)
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)

	def connections_add(self, con):
		return self.connection_set.add(con)

	def connections_all(self):
		return self.connection_set.all()

	def is_tinc(self):
		return type=='router' or type=='switch' or type=='hub'

	def is_internet(self):
		return type=='real'

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("name", self.name)
		dom.setAttribute("type", self.type)
		for con in self.connections_all():
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

	def write_aux_files(self):
		if self.is_tinc():
			self.tinc.write_aux_files()
		if self.is_internet():
			self.internet.write_aux_files()
	
	def write_control_script(self, host, script, fd):
		if self.is_tinc():
			self.tinc.write_control_script(host, script, fd)
		if self.is_internet():
			self.internet.write_control_script(host, script, fd)

	def __unicode__(self):
		return self.name


class Connection(models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(Interface)
	bridge_id = models.IntegerField()
	bridge_special_name = models.CharField(max_length=15)

	def init (self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
		self.bridge_id = hosts.next_free_bridge(self.interface.device.host)
		self.save()

	def is_emulated(self):
		try:
			self.emulatedconnection
			return True
		except:
			return False

	def bridge_name(self):
		if self.bridge_special_name:
			return self.bridge_special_name
		return "gbr_" + self.bridge_id

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("device", self.interface.device.name)
		dom.setAttribute("interface", self.interface.name)
		if self.is_emulated():
			self.emulatedconnection.encode_xml(dom, doc, internal)

	def decode_xml(self, dom):
		device_name = dom.getAttribute("device")
		device = self.connector.topology.devices_get(device_name)
		iface_name = dom.getAttribute("interface")
		self.interface = device.interfaces_get(iface_name)
		
	def write_aux_files(self):
		pass
	
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

	def __unicode__(self):
		return str(self.connector) + "<->" + str(self.interface)
