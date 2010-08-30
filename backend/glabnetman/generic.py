# -*- coding: utf-8 -*-

from django.db import models

import hosts, util, fault, re, tasks

class User():
	def __init__ (self, name, is_user, is_admin):
		self.name = name
		self.is_user = is_user
		self.is_admin = is_admin

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

class Device(models.Model):
	TYPE_OPENVZ="openvz"
	TYPE_KVM="kvm"
	TYPE_DHCPD="dhcpd"
	TYPES = ( (TYPE_OPENVZ, 'OpenVZ'), (TYPE_KVM, 'KVM'), (TYPE_DHCPD, 'DHCP server') )
	name = models.CharField(max_length=20)
	from topology import Topology
	topology = models.ForeignKey(Topology)
	type = models.CharField(max_length=10, choices=TYPES)
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	pos = models.CharField(max_length=10, null=True)
	host = models.ForeignKey(hosts.Host)
	hostgroup = models.ForeignKey(hosts.HostGroup, null=True)

	def interfaces_get(self, name):
		return self.interface_set.get(name=name)

	def interfaces_add(self, iface):
		return self.interface_set.add(iface)

	def interfaces_all(self):
		return self.interface_set.all()

	def upcast(self):
		if self.is_dhcpd():
			return self.dhcpddevice.upcast()
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
			dom.setAttribute("state", self.state)
		for iface in self.interfaces_all():
			x_iface = doc.createElement ( "interface" )
			iface.upcast().encode_xml(x_iface, doc, internal)
			dom.appendChild(x_iface)
		dom.setAttribute("pos", self.pos)
		
	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		self.type = dom.getAttribute("type")
		self.pos = dom.getAttribute("pos")
		util.get_attr(dom, "hostgroup", default=None)
		
	def start(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task.subtasks_total = 1
		util.start_thread(self.upcast().start_run, task)
		return task.id
		
	def stop(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		task.subtasks_total = 1
		util.start_thread(self.upcast().stop_run, task)
		return task.id

	def prepare(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.PREPARED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task.subtasks_total = 1
		util.start_thread(self.upcast().prepare_run, task)
		return task.id

	def destroy(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task.subtasks_total = 1
		util.start_thread(self.upcast().destroy_run, task)
		return task.id

	def start_run(self, task):
		pass

	def stop_run(self, task):
		pass

	def prepare_run(self, task):
		pass

	def destroy_run(self, task):
		pass

	def change_possible(self, dom):
		if not self.hostgroup == util.get_attr(dom, "hostgroup", self.hostgroup):
			if self.state == State.PREPARED or self.state == State.STARTED: 
				raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Cannot change host of deployed device")

	def __unicode__(self):
		return self.name
		
		
class Interface(models.Model):
	name = models.CharField(max_length=5)
	device = models.ForeignKey(Device)
	
	def init(self, device, dom):
		self.device = device
		self.decode_xml(dom)
		if not re.match("eth(\d+)", self.name):
			raise fault.new(fault.INVALID_INTERFACE_NAME, "Invalid interface name: %s" % self.name)
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
	state = models.CharField(max_length=10, choices=((State.CREATED, State.CREATED), (State.PREPARED, State.PREPARED), (State.STARTED, State.STARTED)), default=State.CREATED)
	pos = models.CharField(max_length=10, null=True)

	def connections_add(self, con):
		return self.connection_set.add(con)

	def connections_all(self):
		return self.connection_set.all()

	def connections_get(self, interface):
		return self.connection_set.get(interface=interface)

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
		if internal:
			dom.setAttribute("state", self.state)
		for con in self.connections_all():
			x_con = doc.createElement ( "connection" )
			con.upcast().encode_xml(x_con, doc, internal)
			dom.appendChild(x_con)
		dom.setAttribute("pos", self.pos)

	def decode_xml(self, dom):
		self.name = dom.getAttribute("id")
		self.type = dom.getAttribute("type")
		self.pos = dom.getAttribute("pos")

	def start(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task.subtasks_total = 1
		util.start_thread(self.upcast().start_run, task)
		return task.id
		
	def stop(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.CREATED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Not yet prepared")
		task.subtasks_total = 1
		util.start_thread(self.upcast().stop_run, task)
		return task.id

	def prepare(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.PREPARED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already prepared")
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task.subtasks_total = 1
		util.start_thread(self.upcast().prepare_run, task)
		return task.id

	def destroy(self):
		if self.topology.is_busy():
			raise fault.new(fault.TOPOLOGY_BUSY, "topology is busy with a task")
		task = tasks.TaskStatus()
		self.topology.task = task.id
		if self.state == State.STARTED:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Already started")
		task.subtasks_total = 1
		util.start_thread(self.upcast().destroy_run, task)
		return task.id

	def start_run(self, task):
		for con in self.connections_all():
			con.upcast().start_run(task)

	def stop_run(self, task):
		for con in self.connections_all():
			con.upcast().stop_run(task)

	def prepare_run(self, task):
		for con in self.connections_all():
			con.upcast().prepare_run(task)

	def destroy_run(self, task):
		for con in self.connections_all():
			con.upcast().destroy_run(task)

	def __unicode__(self):
		return self.name

	def change_run(self, dom, task):
		cons=set()
		for x_con in dom.getElementsByTagName("connection"):
			try:
				device_name = x_con.getAttribute("device")
				device = self.topology.devices_get(device_name)
				iface_name = x_con.getAttribute("interface")
				iface = device.interfaces_get(iface_name)
			except Device.DoesNotExist:
				raise fault.new(fault.UNKNOWN_INTERFACE, "Unknown connection device %s" % device_name)
			except Interface.DoesNotExist:
				raise fault.new(fault.UNKNOWN_INTERFACE, "Unknown connection interface %s.%s" % (device_name, iface_name))
			try:
				con = self.connections_get(iface)
				con.upcast().change_run(x_con, task)
				cons.add(con.interface)				
			except Connection.DoesNotExist:
				#new connection
				con = self.add_connection(x_con)
				if self.state == State.STARTED:
					con.start_run(task)
				cons.add(con.interface)
		for con in self.connections_all():
			if not con.interface in cons:
				#deleted connection
				if self.state == State.STARTED:
					con.stop_run(task)
				con.delete()
		self.save()
				
class Connection(models.Model):
	connector = models.ForeignKey(Connector)
	interface = models.OneToOneField(Interface)
	bridge_id = models.IntegerField()
	bridge_special_name = models.CharField(max_length=15, null=True)

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
		try:
			device_name = dom.getAttribute("device")
			device = self.connector.topology.devices_get(device_name)
			iface_name = dom.getAttribute("interface")
			self.interface = device.interfaces_get(iface_name)
			try:
				if not self.interface.connection == self:
					raise fault.new(fault.DUPLICATE_INTERFACE_CONNECTION, "Interface %s is connected to %s and %s" % (self.interface, self.interface.connection, self) )
			except Connection.DoesNotExist:
				pass
		except Device.DoesNotExist:
			raise fault.new(fault.UNKNOWN_INTERFACE, "Unknown connection device %s" % device_name)
		except Interface.DoesNotExist:
			raise fault.new(fault.UNKNOWN_INTERFACE, "Unknown connection interface %s.%s" % (device_name, iface_name))
					
	def start_run(self, task):
		host = self.interface.device.host
		if not self.bridge_special_name:
			host.execute("brctl addbr %s" % self.bridge_name(), task)
			host.execute("ip link set %s up" % self.bridge_name(), task)

	def stop_run(self, task):
		host = self.interface.device.host
		if not self.bridge_special_name:
			host.execute("ip link set %s down" % self.bridge_name(), task)
			#host.execute("brctl delbr %s" % self.bridge_name(), task)

	def change_run(self, dom, task):
		pass

	def prepare_run(self, task):
		pass

	def destroy_run(self, task):
		pass

	def __unicode__(self):
		return str(self.connector) + "<->" + str(self.interface)
