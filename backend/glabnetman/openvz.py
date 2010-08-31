# -*- coding: utf-8 -*-

from django.db import models

import generic, util, hosts, hashlib, config, fault, os, uuid

class OpenVZDevice(generic.Device):
	openvz_id = models.IntegerField()
	root_password = models.CharField(max_length=50, null=True)
	template = models.CharField(max_length=30)
	vnc_port = models.IntegerField()
		
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.template = hosts.get_template("openvz", self.template)
		if not self.template:
			raise fault.new(fault.NO_SUCH_TEMPLATE, "Template not found for %s" % self)
		self.host = hosts.get_best_host(self.hostgroup)
		self.openvz_id = self.host.next_free_vm_id()
		self.vnc_port = self.host.next_free_port()
		self.save()
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = ConfiguredInterface()
			iface.init(self, interface)
			self.interfaces_add(iface)
	
	def upcast(self):
		return self

	def vnc_password(self):
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.name))
		m.update(str(self.openvz_id))
		m.update(str(self.vnc_port))
		m.update(str(self.topology.owner))
		return m.hexdigest()
	
	def encode_xml(self, dom, doc, internal):
		generic.Device.encode_xml(self, dom, doc, internal)
		dom.setAttribute("template", self.template)
		if self.root_password:
			dom.setAttribute("root_password", self.root_password)
		if internal:
			dom.setAttribute("openvz_id", str(self.openvz_id))
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")
		self.root_password = dom.getAttribute("root_password")

	def start_run(self, task):
		generic.Device.start_run(self, task)
		for iface in self.interfaces_all():
			bridge = self.bridge_name(iface)
			self.host.execute("brctl addbr %s" % bridge, task)
			self.host.execute("ip link set %s up" % bridge, task)
		self.host.execute("vzctl start %s --wait" % self.openvz_id, task)
		for iface in self.interfaces_all():
			if iface.is_configured():				
				iface.upcast().start_run(task)
		self.host.execute("( while true; do vncterm -rfbport %s -passwd %s -c vzctl enter %s ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.vnc_port, self.vnc_password(), self.openvz_id, self.name ), task)
		self.state = generic.State.STARTED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Device.stop_run(self, task)
		self.host.execute("cat vnc-%s.pid | xargs kill" % self.name, task)
		self.host.execute("vzctl stop %s" % self.openvz_id, task)
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Device.prepare_run(self, task)
		self.host.execute("vzctl create %s --ostemplate %s" % ( self.openvz_id, self.template ), task)
		self.host.execute("vzctl set %s --devices c:10:200:rw  --capability net_admin:on --save" % self.openvz_id, task)
		if self.root_password:
			self.host.execute("vzctl set %s --userpasswd root:%s --save" % ( self.openvz_id, self.root_password ), task)
		self.host.execute("vzctl set %s --hostname %s_%s --save" % ( self.openvz_id, self.topology.name, self.name ), task)
		for iface in self.interfaces_all():
			iface.upcast().prepare_run(task)
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Device.destroy_run(self, task)
		self.host.execute("vzctl destroy %s" % self.openvz_id, task)
		self.state = generic.State.CREATED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def change_possible(self, dom):
		generic.Device.change_possible(self, dom)
		if not self.template == util.get_attr(dom, "template", self.template):
			if self.state == "started" or self.state == "prepared":
				raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Template of openvz vm %s cannot be changed" % self.name)

	def change_run(self, dom, task):
		"""
		Adapt this device to the new device
		"""
		self.template = util.get_attr(dom, "template", self.template)
		self.root_password = util.get_attr(dom, "root_password")
		if self.root_password and ( self.state == "prepared" or self.state == "started" ):
			self.host.execute("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ), task )
		ifaces=set()
		for x_iface in dom.getElementsByTagName("interface"):
			name = x_iface.getAttribute("id")
			ifaces.add(name)
			try:
				iface = self.interfaces_get(name)
				iface = iface.upcast()
				iface.decode_xml(x_iface)
			except generic.Interface.DoesNotExist:
				iface = ConfiguredInterface()
				iface.init(self, x_iface)
				iface.save()
				self.interfaces_add(iface)
				if self.state == "prepared" or self.state == "started":
					iface.prepare_run(task)
			if self.state == "started":
				iface.start_run(task)
		for iface in self.interfaces_all():
			if not iface.name in ifaces:
				if self.state == "prepared" or self.state == "started":
					self.host.execute("vzctl set %s --netif_del %s --save\n" % ( self.openvz_id, iface.name ), task )
				iface.delete()
		self.save()

	def upload_supported(self):
		return self.state == generic.State.CREATED or self.state == generic.State.PREPARED

	def upload_image(self, filename, task):
		task.subtasks_total=4
		tmp_id = uuid.uuid1()
		remote_filename= "/tmp/glabnetman-%s" % tmp_id
		self.host.upload(filename, remote_filename, task)
		task.subtasks_done = task.subtasks_done + 1
		if self.state == generic.State.PREPARED:
			self.host.execute("vzctl delete %s" % self.openvz_id, task)
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("vzrestore %s %s" % ( remote_filename, self.openvz_id ), task)
		self.state = generic.State.PREPARED
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("rm %s" % remote_filename, task)
		os.remove(filename)
		task.done()

	def download_supported(self):
		return self.state == generic.State.PREPARED or self.state == generic.State.STARTED

	def download_image(self):
		tmp_id = uuid.uuid1()
		filename = "/tmp/glabnetman-%s" % tmp_id
		self.host.execute("mkdir -p %s" % filename)
		self.host.execute("vzdump --compress --dumpdir %s --suspend %s " % ( filename, self.openvz_id ) )
		self.host.download("%s/*.tgz" % filename, filename)
		self.host.execute("rm -r %s" % filename)
		return filename

class ConfiguredInterface(generic.Interface):
	use_dhcp = models.BooleanField()
	ip4address = models.CharField(max_length=18, null=True)
	gateway = models.CharField(max_length=15, null=True)

	def init(self, device, dom):
		self.device = device
		self.decode_xml(dom)
		self.save()

	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Interface.encode_xml(self, dom, doc, internal)
		if self.use_dhcp:
			dom.setAttribute("use_dhcp", str(self.use_dhcp).lower())
		if self.ip4address:
			dom.setAttribute("ip4address", self.ip4address)
		if self.gateway:
			dom.setAttribute("gateway", self.gateway)
		
	def decode_xml(self, dom):
		generic.Interface.decode_xml(self, dom)
		self.use_dhcp = util.parse_bool(util.get_attr(dom, "use_dhcp", default="false"))
		self.ip4address = util.get_attr(dom, "ip4address", default=None)
		self.gateway = util.get_attr(dom, "gateway", default=None)
		
	def start_run(self, task):
		openvz_id = self.device.upcast().openvz_id
		bridge = self.device.upcast().bridge_name(self)
		if self.ip4address:
			self.device.host.execute("vzctl exec %s ip addr add %s dev %s" % ( openvz_id, self.ip4address, self.name ), task) 
			self.device.host.execute("vzctl exec %s ip link set up dev %s" % ( openvz_id, self.name ), task) 
		if self.gateway:
			self.device.host.execute("vzctl exec %s route add default gw %s" % ( openvz_id, self.gateway), task) 
		if self.use_dhcp:
			self.device.host.execute("vzctl exec %s \"[ -e /sbin/dhclient ] && /sbin/dhclient %s\"" % ( openvz_id, self.name ), task)
			self.device.host.execute("vzctl exec %s \"[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s\"" % ( openvz_id, self.name ), task)					
		self.device.host.execute("ip link set %s up" % bridge, task)

	def prepare_run(self, task):
		openvz_id = self.device.upcast().openvz_id
		bridge = self.device.upcast().bridge_name(self)
		self.device.host.execute("vzctl set %s --netif_add %s --save" % ( openvz_id, self.name ), task)
		self.device.host.execute("vzctl set %s --ifname %s --host_ifname veth%s.%s --bridge %s --save" % ( openvz_id, self.name, openvz_id, self.name, bridge ), task)