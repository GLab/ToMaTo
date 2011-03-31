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

import fault, hosts, attributes

class State(): #pylint: disable-msg=W0232
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

class Device(models.Model):
	TYPE_OPENVZ="openvz"
	TYPE_KVM="kvm"
	TYPES = ( (TYPE_OPENVZ, 'OpenVZ'), (TYPE_KVM, 'KVM') )
	name = models.CharField(max_length=20)
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	host = models.ForeignKey(hosts.Host, null=True)
	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)

	def interface_set_get(self, name):
		return self.interface_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def interface_set_add(self, iface):
		return self.interface_set.add(iface) # pylint: disable-msg=E1101

	def interface_set_all(self):
		return self.interface_set.all() # pylint: disable-msg=E1101

	def upcast(self):
		if self.is_kvm():
			return self.kvmdevice.upcast() # pylint: disable-msg=E1101
		if self.is_openvz():
			return self.openvzdevice.upcast() # pylint: disable-msg=E1101
		return self

	def is_openvz(self):
		return self.type == Device.TYPE_OPENVZ

	def is_kvm(self):
		return self.type == Device.TYPE_KVM
	
	def host_preferences(self):
		prefs = ObjectPreferences(True)
		for h in hosts.get_hosts(self.attributes.get("hostgroup")):
			if h.enabled:
				prefs.add(h, 1.0 - len(h.device_set.all())/100.0)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def host_options(self):
		options = self.host_preferences()
		for iface in self.interface_set_all():
			options = options.combine(iface.connection.connector.upcast().host_preferences())
		return options

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
		except: #pylint: disable-msg=W0702
			return None		
	
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
		for iface in self.interface_set_all():
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

	def start_run(self):
		pass

	def stop_run(self):
		pass

	def prepare_run(self):
		pass

	def destroy_run(self):
		pass
	
	def configure(self, properties):
		if "hostgroup" in properties:
			assert self.state == State.CREATED, "Cannot change hostgroup of prepared device: %s" % self.name
			if properties["hostgroup"] == "auto":
				properties["hostgroup"] = ""
		for key in properties:
			self.attributes[key] = properties[key]
		self.save()

	def update_resource_usage(self):
		res = self.upcast().get_resource_usage()
		for key in res:
			self.attributes["resources_%s" % key] = res[key]

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
		res = {"attrs": {"host": str(self.host) if self.host else None,
					"name": self.name, "type": self.type, "state": self.state,
					"download_supported": self.download_supported(), "upload_supported": self.upload_supported() 
					},
			"interfaces": dict([[i.name, i.upcast().to_dict(auth)] for i in self.interface_set_all()]),
		}
		res["attrs"].update(self.attributes.items())
		return res
	
	def upload_image_grant(self, redirect):
		import uuid
		if self.host:
			filename = str(uuid.uuid1())
			redirect = redirect % filename
			return {"upload_url": self.host.upload_grant(filename, redirect), "redirect_url": redirect}
		else:
			return None
	
	def download_image_uri(self):
		if self.host:
			filename = self.upcast().prepare_downloadable_image()
			return self.host.download_grant(filename, filename)
		else:
			return None
			
	def use_uploaded_image(self, filename):
		return self.topology.start_task(self.upcast().use_uploaded_image_run, filename).id
			
			
class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)
	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)

	def is_configured(self):
		try:
			self.configuredinterface # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False
	
	def is_connected(self):
		try:
			self.connection # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False	
	
	def configure(self, properties):
		for key in properties:
			self.attributes[key] = properties[key]
		self.save()

	def upcast(self):
		if self.is_configured():
			return self.configuredinterface.upcast() # pylint: disable-msg=E1101
		return self

	def __unicode__(self):
		return str(self.device.name)+"."+str(self.name)
		
	def to_dict(self, auth):
		"""
		Prepares an interface for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the interface
		@rtype: dict
		"""
		res = {"attrs": {"name": self.name}}
		res["attrs"].update(self.attributes.items())
		return res


class Connector(models.Model):
	TYPES = ( ('router', 'Router'), ('switch', 'Switch'), ('hub', 'Hub'), ('special', 'Special feature') )
	name = models.CharField(max_length=20)
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)

	def connection_set_add(self, con):
		return self.connection_set.add(con) # pylint: disable-msg=E1101

	def connection_set_all(self):
		return self.connection_set.all() # pylint: disable-msg=E1101

	def connection_set_get(self, interface):
		return self.connection_set.get(interface=interface).upcast() # pylint: disable-msg=E1101

	def is_tinc(self):
		return self.type=='router' or self.type=='switch' or self.type=='hub'

	def is_special(self):
		return self.type=='special'

	def upcast(self):
		if self.is_tinc():
			return self.tincconnector.upcast() # pylint: disable-msg=E1101
		if self.is_special():
			return self.specialfeatureconnector.upcast() # pylint: disable-msg=E1101
		return self

	def host_preferences(self):
		prefs = ObjectPreferences()
		# keep it local
		for c in self.connection_set_all():
			dev = c.interface.device
			if dev.host:
				prefs.add(dev.host, -0.1)
				for h in hosts.get_hosts(dev.host.group):
					prefs.add(h, 0.01)
		#print "Host preferences for %s: %s" % (self, prefs) 
		return prefs

	def affected_hosts(self):
		return hosts.Host.objects.filter(device__interface__connection__connector=self).distinct() # pylint: disable-msg=E1101

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

	def start_run(self):
		for con in self.connection_set_all():
			con.upcast().start_run()

	def stop_run(self):
		for con in self.connection_set_all():
			con.upcast().stop_run()

	def prepare_run(self):
		for con in self.connection_set_all():
			if con.interface.device.state == State.CREATED:
				raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Device must be prepared first: %s" % con.interface.device )
		for con in self.connection_set_all():
			con.upcast().prepare_run()

	def destroy_run(self):
		for con in self.connection_set_all():
			con.upcast().destroy_run()

	def __unicode__(self):
		return self.name
				
	def update_resource_usage(self):
		res = self.upcast().get_resource_usage()
		for key in res:
			self.attributes["resources_%s" % key] = res[key]
	
	def bridge_name(self, interface):
		return "gbr_%s" % interface.connection.bridge_id()

	def configure(self, properties):
		for key in properties:
			self.attributes[key] = properties[key]
		self.save()

	def to_dict(self, auth):
		"""
		Prepares a connector for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the connector
		@rtype: dict
		"""
		res = {"attrs": {"name": self.name, "type": self.type, "state": self.state},
			"connections": dict([[str(c.interface), c.upcast().to_dict(auth)] for c in self.connection_set_all()]),
			}
		res["attrs"].update(self.attributes.items())
		return res


class Connection(models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(Interface)
	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)

	def is_emulated(self):
		try:
			self.emulatedconnection # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False

	def upcast(self):
		if self.is_emulated():
			return self.emulatedconnection.upcast() # pylint: disable-msg=E1101
		return self

	def bridge_id(self):
		if not self.attributes.get("bridge_id"):
			self.attributes["bridge_id"] = self.interface.device.host.next_free_bridge()
		return self.attributes["bridge_id"]

	def bridge_name(self):
		return self.connector.upcast().bridge_name(self.interface)
				
	def start_run(self):
		host = self.interface.device.host
		if not self.connector.is_special():
			host.bridge_create(self.bridge_name())
			host.execute("ip link set %s up" % self.bridge_name())

	def stop_run(self):
		host = self.interface.device.host
		if not host:
			return
		if not self.connector.is_special():
			host.execute("ip link set %s down" % self.bridge_name())

	def prepare_run(self):
		if not self.attributes.get("bridge_id"):
			self.attributes["bridge_id"] = self.interface.device.host.next_free_bridge()

	def destroy_run(self):
		del self.attributes["bridge_id"]

	def __unicode__(self):
		return str(self.connector) + "<->" + str(self.interface)

	def configure(self, properties):
		for key in properties:
			self.attributes[key] = properties[key]
		self.save()

	def to_dict(self, auth):
		"""
		Prepares a connection for serialization.
		
		@type auth: boolean
		@param auth: Whether to include confidential information
		@return: a dict containing information about the connection
		@rtype: dict
		"""
		res = {"interface": str(self.interface), "attrs":{}}
		res["attrs"].update(self.attributes.items())
		return res

class ObjectPreferences:
	def __init__(self, exclusive=False):
		self.exclusive = exclusive
		self.objects = []
		self.values = []
	def add(self, obj, value=1.0):
		try:
			index = self.objects.index(obj)
			self.values[index]+=value
		except:
			self.objects.append(obj)
			self.values.append(value)
	def remove(self, obj):
		try:
			index = self.objects.index(obj)
			del self.objects[index]
			del self.values[index]
		except:
			pass
	def getValue(self, obj):
		try:
			index = self.objects.index(obj)
			return self.values[index]
		except:
			return None
	def contains(self, obj):
		return not (self.getValue(obj) is None)
	def combine(self, other):
		if other.exclusive and not self.exclusive:
			return other.combine(self)
		res = ObjectPreferences(self.exclusive or other.exclusive)
		if self.exclusive:
			for o in self.objects:
				val = self.getValue(o)
				oval = other.getValue(o)
				if not (oval is None and other.exclusive):
					res.add(o, (oval + val) if oval else val)
		else:
			for o in self.objects:
				res.add(o, self.getValue(o))
			for o in other.objects:
				res.add(o, other.getValue(o))
		return res
	def best(self):
		max_val = None
		best = None
		i = 0
		while i < len(self.values):
			if max_val is None or max_val < self.values[i]:
				max_val = self.values[i]
				best = self.objects[i]
			i=i+1
		return best
	def __str__(self):
		strs = []
		i=0
		while i < len(self.values):
			strs.append("%s: %s" %(self.objects[i], self.values[i]))
			i=i+1
		type = "exclusive" if self.exclusive else "hint"
		return type + ":{" + (", ".join(strs)) + "}"