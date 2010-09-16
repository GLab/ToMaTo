# -*- coding: utf-8 -*-

from django.db import models

import generic, util, hosts, hashlib, config, fault, os, uuid

class OpenVZDevice(generic.Device):
	openvz_id = models.IntegerField(null=True)
	root_password = models.CharField(max_length=50, null=True)
	template = models.CharField(max_length=30)
	vnc_port = models.IntegerField(null=True)
	gateway = models.CharField(max_length=15, null=True)
		
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.template = hosts.get_template("openvz", self.template)
		if not self.template:
			raise fault.new(fault.NO_SUCH_TEMPLATE, "Template not found for %s" % self)
		self.host = hosts.get_best_host(self.hostgroup)
		self.save()
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = ConfiguredInterface()
			iface.init(self, interface)
			self.interfaces_add(iface)
	
	def upcast(self):
		return self

	def vnc_password(self):
		if not self.vnc_port:
			return "---" 
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
		if self.gateway:
			dom.setAttribute("gateway", self.gateway)
		if internal:
			if self.openvz_id:
				dom.setAttribute("openvz_id", str(self.openvz_id))
			if self.vnc_port:
				dom.setAttribute("vnc_port", str(self.vnc_port))
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")
		self.root_password = dom.getAttribute("root_password")
		self.gateway = util.get_attr(dom, "gateway", default=None)

	def get_state(self, task):
		if config.remote_dry_run:
			return self.state
		if not self.openvz_id:
			return generic.State.CREATED
		res = self.host.execute("vzctl status %s" % self.openvz_id, task)
		if "exist" in res and "running" in res:
			return generic.State.STARTED
		if "exist" in res and "down" in res:
			return generic.State.PREPARED
		if "deleted" in res:
			return generic.State.CREATED
		raise fault.new(fault.UNKNOWN, "Unable to determine openvz state for %s: %s" % ( self, res ) )

	def start_run(self, task):
		generic.Device.start_run(self, task)
		for iface in self.interfaces_all():
			bridge = self.bridge_name(iface)
			self.host.bridge_create(bridge)
			self.host.execute("ip link set %s up" % bridge, task)
		self.host.execute("vzctl start %s --wait" % self.openvz_id, task)
		for iface in self.interfaces_all():
			if iface.is_configured():
				iface = iface.upcast()
				iface.start_run(task)
				assert self.host.interface_bridge(iface.interface_name()) == self.bridge_name(iface), "Interface %s not connect to bridge %s" % (iface.interface_name(), self.bridge_name(iface))
		if self.gateway:
			self.host.execute("vzctl exec %s route add default gw %s" % ( self.openvz_id, self.gateway), task) 
		if not self.vnc_port:
			self.vnc_port = self.host.next_free_port()
			self.save()		
		self.host.free_port(self.vnc_port, task)		
		self.host.execute("( while true; do vncterm -rfbport %s -passwd %s -c vzctl enter %s ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.vnc_port, self.vnc_password(), self.openvz_id, self.name ), task)
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.STARTED, "VM is not running"
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Device.stop_run(self, task)
		self.host.execute("cat vnc-%s.pid | xargs -r kill" % self.name, task)
		self.vnc_port=None
		self.host.execute("vzctl stop %s" % self.openvz_id, task)
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Device.prepare_run(self, task)
		self.template = hosts.get_template("openvz", self.template)
		if not self.openvz_id:
			self.openvz_id = self.host.next_free_vm_id()
			self.save()				
		self.host.execute("vzctl create %s --ostemplate %s" % ( self.openvz_id, self.template ), task)
		self.host.execute("vzctl set %s --devices c:10:200:rw  --capability net_admin:on --save" % self.openvz_id, task)
		if self.root_password:
			self.host.execute("vzctl set %s --userpasswd root:%s --save" % ( self.openvz_id, self.root_password ), task)
		self.host.execute("vzctl set %s --hostname %s-%s --save" % ( self.openvz_id, self.topology.name.replace("_","-"), self.name ), task)
		for iface in self.interfaces_all():
			iface.upcast().prepare_run(task)
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Device.destroy_run(self, task)
		if self.openvz_id:
			self.host.execute("vzctl destroy %s" % self.openvz_id, task)
		self.openvz_id=None
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.CREATED, "VM still exists"
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
		generic.Device.change_run(self, dom, task)
		self.template = util.get_attr(dom, "template", self.template)
		self.template = hosts.get_template("openvz", self.template)
		self.root_password = util.get_attr(dom, "root_password")
		if self.root_password and ( self.state == "prepared" or self.state == "started" ):
			self.host.execute("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ), task )
		self.gateway = util.get_attr(dom, "gateway", self.gateway)
		ifaces=set()
		for x_iface in dom.getElementsByTagName("interface"):
			name = x_iface.getAttribute("id")
			ifaces.add(name)
			try:
				iface = self.interfaces_get(name)
				iface = iface.upcast()
				iface.decode_xml(x_iface)
				iface.save()
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
		return self.state == generic.State.PREPARED

	def upload_image(self, filename, task):
		task.subtasks_total=2
		tmp_id = uuid.uuid1()
		remote_filename= "/tmp/glabnetman-%s" % tmp_id
		self.host.upload(filename, remote_filename, task)
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("rm -rf /var/lib/vz/private/%s" % self.openvz_id, task)
		self.host.execute("mkdir /var/lib/vz/private/%s" % self.openvz_id, task)
		self.host.execute("tar -xzf %s -C /var/lib/vz/private/%s" % ( remote_filename, self.openvz_id ), task)
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("rm %s" % remote_filename, task)
		os.remove(filename)
		task.done()

	def download_supported(self):
		return self.state == generic.State.PREPARED

	def download_image(self):
		tmp_id = uuid.uuid1()
		filename = "/tmp/glabnetman-%s" % tmp_id
		self.host.execute("tar --numeric-owner -czf %s -C /var/lib/vz/private/%s . " % ( filename, self.openvz_id ) )
		self.host.download("%s" % filename, filename)
		self.host.execute("rm %s" % filename)
		return filename

class ConfiguredInterface(generic.Interface):
	use_dhcp = models.BooleanField()
	ip4address = models.CharField(max_length=18, null=True)

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

	def interface_name(self):
		return "veth%s.%s" % ( self.device.upcast().openvz_id, self.name )
		
	def decode_xml(self, dom):
		generic.Interface.decode_xml(self, dom)
		self.use_dhcp = util.parse_bool(util.get_attr(dom, "use_dhcp", default="false"))
		self.ip4address = util.get_attr(dom, "ip4address", default=None)
		
	def start_run(self, task):
		openvz_id = self.device.upcast().openvz_id
		bridge = self.device.upcast().bridge_name(self)
		self.device.host.bridge_connect(bridge, self.interface_name())
		if self.ip4address:
			self.device.host.execute("vzctl exec %s ip addr add %s dev %s" % ( openvz_id, self.ip4address, self.name ), task) 
			self.device.host.execute("vzctl exec %s ip link set up dev %s" % ( openvz_id, self.name ), task) 
		if self.use_dhcp:
			self.device.host.execute("vzctl exec %s \"[ -e /sbin/dhclient ] && /sbin/dhclient %s\"" % ( openvz_id, self.name ), task)
			self.device.host.execute("vzctl exec %s \"[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s\"" % ( openvz_id, self.name ), task)					
		self.device.host.execute("ip link set %s up" % bridge, task)

	def prepare_run(self, task):
		openvz_id = self.device.upcast().openvz_id
		self.device.host.execute("vzctl set %s --netif_add %s --save" % ( openvz_id, self.name ), task)
		self.device.host.execute("vzctl set %s --ifname %s --host_ifname %s --save" % ( openvz_id, self.name, self.interface_name()), task)		