# -*- coding: utf-8 -*-

from django.db import models

import hosts, util, fault

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

	def interfaces_remove(self, iface):
		return self.interface_set.remove(iface)

	def interfaces_all(self):
		return self.interface_set.all()

	def upcast(self):
		if self.is_dhcpd():
			return self.dhcpdevice.upcast()
		if self.is_kvm():
			return self.kvmdevice.upcast()
		if self.is_openvz():
			return self.openvzdevice.upcast()
		return self

	def is_openvz(self):
		return self.type == Device.TYPE_OPENVZ

	def is_kvm(self):
		return self.type == Device.TYPE_KVM

	def is_dhcpd(self):
		return self.type == Device.TYPE_DHCPD

	def download_supported(self):
		return False
		
	def upload_supported(self):
		return False
		
	def bridge_name(self, interface):
		"""
		Returns the name of the bridge for the connection of the given interface
		Note: This must be 16 characters or less for brctl to work
		@param interface the interface
		"""
		if interface.connection:
			return interface.connection.bridge_name()
		else:
			return None		

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("id", self.name)
		dom.setAttribute("type", self.type)
		if self.hostgroup:
			dom.setAttribute("hostgroup", self.hostgroup)
		if internal:
			dom.setAttribute("host", self.host)
		for iface in self.interfaces_all():
			x_iface = doc.createElement ( "interface" )
			iface.upcast().encode_xml(x_iface, doc, internal)
			dom.appendChild(x_iface)
		
	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		self.type = dom.getAttribute("type")
		util.get_attr(dom, "hostgroup", default=None)
		
	def write_aux_files(self):
		pass
	
	def write_control_script(self, host, script, fd):
		pass

	def change_possible(self, dom):
		if not self.hostgroup == util.get_attr(dom, "hostgroup", self.hostgroup):
			from topology import State
			if self.topology.state == State.PREPARED or self.topology.state == State.STARTED: 
				raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Cannot change host of deployed device")

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
	
	def upcast(self):
		if self.is_configured():
			return self.configuredinterface.upcast()
		return self

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("id", self.name)

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
		return self.type=='router' or self.type=='switch' or self.type=='hub'

	def is_internet(self):
		return self.type=='real'

	def upcast(self):
		if self.is_tinc():
			return self.tincconnector.upcast()
		if self.is_internet():
			return self.internetconnector.upcast()
		return self

	def affected_hosts(self):
		return hosts.Host.objects.filter(device__interface__connection__connector=self).distinct()

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("id", self.name)
		dom.setAttribute("type", self.type)
		for con in self.connections_all():
			x_con = doc.createElement ( "connection" )
			con.upcast().encode_xml(x_con, doc, internal)
			dom.appendChild(x_con)

	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		self.type = dom.getAttribute("type")

	def write_aux_files(self):
		pass
	
	def write_control_script(self, host, script, fd):
		pass

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
		self.bridge_id = self.interface.device.host.next_free_bridge()		
		self.save()

	def is_emulated(self):
		try:
			self.emulatedconnection
			return True
		except:
			return False

	def upcast(self):
		if self.is_emulated():
			return self.emulatedconnection.upcast()
		return self

	def bridge_name(self):
		if self.bridge_special_name:
			return self.bridge_special_name
		return "gbr_%s" % self.bridge_id

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("device", self.interface.device.name)
		dom.setAttribute("interface", self.interface.name)

	def decode_xml(self, dom):
		device_name = dom.getAttribute("device")
		device = self.connector.topology.devices_get(device_name)
		iface_name = dom.getAttribute("interface")
		self.interface = device.interfaces_get(iface_name)
		#FIXME: raise fault when device/interface not found
		
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
