# -*- coding: utf-8 -*-
from django.db import models

class HostGroup(models.Model):
	name = models.CharField(max_length=10)
	
class Host(models.Model):
	group = models.ForeignKey(HostGroup)
	hostname = models.CharField(max_length=50)

class Topology(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=30, blank=True)

class Device(models.Model):
	TYPES = ( ('openvz', 'OpenVZ'), ('kvm', 'KVM'), ('dhcpd', 'DHCP server') )
	name = models.CharField(max_length=20)
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	host = models.ForeignKey(Host)
	hostgroup = models.ForeignKey(HostGroup, null=True)

class OpenVZDevice(Device):
	openvz_id = models.IntegerField()
	root_password = models.CharField(max_length=50, null=True)
	template = models.CharField(max_length=30)

class KVMDevice(Device):
	kvm_id = models.IntegerField()
	template = models.CharField(max_length=30)

class DhcpdDevice(Device):
	subnet = models.CharField(max_length=15)
	netmask = models.CharField(max_length=15)
	range = models.CharField(max_length=31)
	gateway = models.CharField(max_length=15)
	nameserver = models.CharField(max_length=15)

class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)
	
class ConfiguredInterface(Interface):
	use_dhcp = models.NullBooleanField()
	ip4address = models.CharField(max_length=15, null=True)
	ip4netmask = models.CharField(max_length=15, null=True)

class Connector(models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('real', 'Real network') )
	name = models.CharField(max_length=20)
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)

class Connection(models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(Interface)
	
class EmulatedConnection(Connection):
	delay = models.IntegerField(null=True)
	bandwidth = models.IntegerField(null=True)
	lossratio = models.FloatField(null=True)