# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.db import models

import hosts, util, fault, re

class State():
	"""
	The state of the element, this is an assigned value. The states are considered to be in order:
	created -> prepared -> started
	created		the element has been created but not prepared
	prepared	all devices have been prepared
	started		the element has been prepared and is currently up and running
	"""
	CREATED="created"
	PREPARED="prepared"
	STARTED="started"

class ResourceSet(models.Model):
	disk = models.IntegerField(default=0)
	memory = models.IntegerField(default=0)
	ports = models.IntegerField(default=0)
	special = models.IntegerField(default=0)

	def clean(self):
		for r in self.resourceentry_set.all():
			r.delete()

	def add(self, set):
		for r in set.resourceentry_set.all():
			self.set(r.type, self.get(r.type) + r.value)

	def set(self, type, value):
		if len(self.resourceentry_set.filter(type=type)) == 0:
			res = ResourceEntry(resource_set=self, type=type, value=value)
			res.save()
			self.resourceentry_set.add(res)
		else:
			res = self.resourceentry_set.all().get(type=type)
			res.value = value
			res.save()
	
	def get(self, type):
		if len(self.resourceentry_set.filter(type=type)) == 0:
			return 0
		else:
			res = self.resourceentry_set.get(type=type)
			return res.value
		
	def decode(self, dict):
		for k, v in dict.items():
			self.set(k, v)
			
	def encode(self):
		dict = {}
		for r in self.resourceentry_set.all():
			dict[r.type] = str(r.value)
		return dict

def add_encoded_resources(r1, r2):
	res = {}
	for k, v in r1.items():
		if k in res:
			res[k] = str(int(res[k]) + int(v))
		else:
			res[k] = v
	for k, v in r2.items():
		if k in res:
			res[k] = str(int(res[k]) + int(v))
		else:
			res[k] = v
	return res

class ResourceEntry(models.Model):
	resource_set = models.ForeignKey(ResourceSet)
	type = models.CharField(max_length=20)
	value = models.BigIntegerField()

class Device(models.Model):
	TYPE_OPENVZ="openvz"
	TYPE_KVM="kvm"
	TYPES = ( (TYPE_OPENVZ, 'OpenVZ'), (TYPE_KVM, 'KVM') )
	name = models.CharField(max_length=20)
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	pos = models.CharField(max_length=10, null=True)
	host = models.ForeignKey(hosts.Host, null=True)
	hostgroup = models.CharField(max_length=10, null=True)
	resources = models.ForeignKey(ResourceSet, null=True)

	def interfaces_get(self, name):
		return self.interface_set.get(name=name).upcast()

	def interfaces_add(self, iface):
		return self.interface_set.add(iface)

	def interfaces_all(self):
		return self.interface_set.all()

	def upcast(self):
		if self.is_kvm():
			return self.kvmdevice.upcast()
		if self.is_openvz():
			return self.openvzdevice.upcast()
		return self

	def is_openvz(self):
		return self.type == Device.TYPE_OPENVZ

	def is_kvm(self):
		return self.type == Device.TYPE_KVM

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
		try:
			return interface.connection.bridge_name()
		except:
			return None		

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("name", self.name)
		dom.setAttribute("type", self.type)
		if self.hostgroup:
			dom.setAttribute("hostgroup", self.hostgroup)
		if internal:
			if self.host:
				dom.setAttribute("host", self.host.name)
			dom.setAttribute("state", self.state)
		for iface in self.interfaces_all():
			x_iface = doc.createElement ( "interface" )
			iface.upcast().encode_xml(x_iface, doc, internal)
			dom.appendChild(x_iface)
		if self.pos:
			dom.setAttribute("pos", self.pos)
		
	def start(self):
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task = self.topology.start_task(self.upcast().start_run)
		task.subtasks_total = 1
		return task.id
		
	def stop(self):
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		task = self.topology.start_task(self.upcast().stop_run)
		task.subtasks_total = 1
		return task.id

	def prepare(self):
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.PREPARED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task = self.topology.start_task(self.upcast().prepare_run)
		task.subtasks_total = 1
		return task.id

	def destroy(self):
		for iface in self.interfaces_all():
			if iface.is_connected():
				con = iface.connection.connector
				if not con.is_special() and not con.state == State.CREATED:
					raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Connector must be destroyed first: %s" % con )		
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task = self.topology.start_task(self.upcast().destroy_run)
		task.subtasks_total = 1
		return task.id

	def start_run(self, task):
		pass

	def stop_run(self, task):
		pass

	def prepare_run(self, task):
		pass

	def destroy_run(self, task):
		pass

	def configure(self, properties, task):
		if "pos" in properties:
			self.pos = properties["pos"]
		if "template" in properties:
			assert self.state == State.CREATED, "Cannot change template of prepared device: %s" % self.name
			if not self.template.startswith("***"):
				self.template = hosts.get_template_name(self.type, properties["template"])
				if not self.template:
					raise fault.new(fault.NO_SUCH_TEMPLATE, "Template not found:" % properties["template"])
		if "hostgroup" in properties:
			assert self.state == State.CREATED, "Cannot change hostgroup of prepared device: %s" % self.name
			self.hostgroup = properties["hostgroup"]
		self.save()

	def update_resource_usage(self):
		res = self.upcast().get_resource_usage()
		if not self.resources:
			r = ResourceSet()
			r.save()
			self.resources = r 
			self.save()
		self.resources.decode(res)
		return self.resources

	def __unicode__(self):
		return self.name
		
	def to_dict(self, auth):
		"""
		Prepares a device for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the device
		@rtype: dict
		"""
		state = str(self.state)
		res = {"name": self.name, "type": self.type, "host": str(self.host),
			"state": state,
			"is_created": state == State.CREATED,
			"is_prepared": state == State.PREPARED,
			"is_started": state == State.STARTED,
			"upload_supported": self.upcast().upload_supported(),
			"download_supported": self.upcast().download_supported(),
			}
		if auth:
			dev = self.upcast()
			if dev.resources:
				res.update(resources=dev.resources.encode())
			if hasattr(dev, "vnc_port") and dev.vnc_port:
				res.update(vnc_port=dev.vnc_port)
			if hasattr(dev, "vnc_password"):
				res.update(vnc_password=dev.vnc_password())
		return res
		
class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)

	def is_configured(self):
		try:
			self.configuredinterface
			return True
		except:
			return False
	
	def is_connected(self):
		try:
			self.connection
			return True
		except:
			return False	
	
	def upcast(self):
		if self.is_configured():
			return self.configuredinterface.upcast()
		return self

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("name", self.name)

	def __unicode__(self):
		return str(self.device.name)+"."+str(self.name)
		

class Connector(models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('special', 'Special feature') )
	name = models.CharField(max_length=20)
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	pos = models.CharField(max_length=10, null=True)
	resources = models.ForeignKey(ResourceSet, null=True)

	def connections_add(self, con):
		return self.connection_set.add(con)

	def connections_all(self):
		return self.connection_set.all()

	def connections_get(self, interface):
		return self.connection_set.get(interface=interface).upcast()

	def is_tinc(self):
		return self.type=='router' or self.type=='switch' or self.type=='hub'

	def is_special(self):
		return self.type=='special'

	def upcast(self):
		if self.is_tinc():
			return self.tincconnector.upcast()
		if self.is_special():
			return self.specialfeatureconnector.upcast()
		return self

	def affected_hosts(self):
		return hosts.Host.objects.filter(device__interface__connection__connector=self).distinct()

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("name", self.name)
		dom.setAttribute("type", self.type)
		if internal:
			dom.setAttribute("state", self.state)
		for con in self.connections_all():
			x_con = doc.createElement ( "connection" )
			con.upcast().encode_xml(x_con, doc, internal)
			dom.appendChild(x_con)
		if self.pos:
			dom.setAttribute("pos", self.pos)

	def start(self):
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task = self.topology.start_task(self.upcast().start_run)
		task.subtasks_total = 1
		return task.id
		
	def stop(self):
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		task = self.topology.start_task(self.upcast().stop_run)
		task.subtasks_total = 1
		return task.id

	def prepare(self):
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.PREPARED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task = self.topology.start_task(self.upcast().prepare_run)
		task.subtasks_total = 1
		return task.id

	def destroy(self):
		self.topology.renew()
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task = self.topology.start_task(self.upcast().destroy_run)
		task.subtasks_total = 1
		return task.id

	def start_run(self, task):
		for con in self.connections_all():
			con.upcast().start_run(task)

	def stop_run(self, task):
		for con in self.connections_all():
			con.upcast().stop_run(task)

	def prepare_run(self, task):
		for con in self.connections_all():
			if con.interface.device.state == State.CREATED:
				raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Device must be prepared first: %s" % con.interface.device )
		for con in self.connections_all():
			con.upcast().prepare_run(task)

	def destroy_run(self, task):
		for con in self.connections_all():
			con.upcast().destroy_run(task)

	def __unicode__(self):
		return self.name

	def configure(self, properties, task):
		if "pos" in properties:
			self.pos = properties["pos"]
		self.save()
				
	def update_resource_usage(self):
		res = self.upcast().get_resource_usage()
		if not self.resources:
			r = ResourceSet()
			r.save()
			self.resources = r 
			self.save()
		self.resources.decode(res)
		return self.resources
	
	def bridge_name(self, interface):
		return "gbr_%s" % interface.connection.bridge_id

	def to_dict(self, auth):
		"""
		Prepares a connector for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the connector
		@rtype: dict
		"""
		state = str(self.state)
		res = {"name": self.name, "type": ("special: %s" % self.upcast().feature_type if self.is_special() else self.type),
			"state": state,
			"is_created": state == State.CREATED,
			"is_prepared": state == State.PREPARED,
			"is_started": state == State.STARTED,
			}
		if auth:
			if self.resources:
				res.update(resources=self.resources.encode())
		return res


class Connection(models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(Interface)
	bridge_id = models.IntegerField(null=True)

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
		return self.connector.upcast().bridge_name(self.interface)

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("interface", "%s.%s" % (self.interface.device.name, self.interface.name))
					
	def start_run(self, task):
		host = self.interface.device.host
		if not self.connector.is_special():
			host.bridge_create(self.bridge_name())
			host.execute("ip link set %s up" % self.bridge_name(), task)

	def stop_run(self, task):
		host = self.interface.device.host
		if not host:
			return
		if not self.connector.is_special():
			host.execute("ip link set %s down" % self.bridge_name(), task)

	def prepare_run(self, task):
		if not self.bridge_id:
			self.bridge_id = self.interface.device.host.next_free_bridge()
			self.save()		

	def destroy_run(self, task):
		self.bridge_id=None
		self.save()

	def __unicode__(self):
		return str(self.connector) + "<->" + str(self.interface)
