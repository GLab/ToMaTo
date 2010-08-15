# -*- coding: utf-8 -*-

from django.db import models

import hosts, topology

class User():
	def __init__ (self, name, is_user, is_admin):
		self.name = name
		self.is_user = is_user
		self.is_admin = is_admin

class Device(models.Model):
	TYPES = ( ('openvz', 'OpenVZ'), ('kvm', 'KVM'), ('dhcpd', 'DHCP server') )
	name = models.CharField(max_length=20)
	topology = models.ForeignKey(topology.Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	host = models.ForeignKey(hosts.Host)
	hostgroup = models.ForeignKey(hosts.HostGroup, null=True)

class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)
	
class Connector(models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('real', 'Real network') )
	name = models.CharField(max_length=20)
	topology = models.ForeignKey(topology.Topology)
	type = models.CharField(max_length=10, choices=TYPES)

class Connection(models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(Interface)
