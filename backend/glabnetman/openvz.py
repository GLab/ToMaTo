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
		if not self.template:
			self.template = config.openvz_default_template
		self.host = hosts.get_best_host(self.hostgroup)
		self.openvz_id = self.host.next_free_vm_id()
		self.vnc_port = self.host.next_free_port()
		self.save()
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = ConfiguredInterface()
			iface.init(self, interface)
			self.interfaces_add(iface)
	
	def vnc_password(self):
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.name))
		m.update(str(self.openvz_id))
		m.update(str(self.vnc_port))
		m.update(str(self.topology.owner))
		return m.hexdigest()
	
	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("template", self.template)
		if self.root_password:
			dom.setAttribute("root_password", self.root_password)
		if internal:
			dom.setAttribute("openvz_id", str(self.openvz_id))
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")
		self.root_password = dom.getAttribute("root_password")

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

	def write_aux_files(self):
		"""
		Write the aux files for this object and its child objects
		"""		
		pass

	def write_control_script(self, host, script, fd):
		"""
		Write the control script for this object and its child objects
		"""
		if script == "prepare":
			fd.write("vzctl create %s --ostemplate %s\n" % ( self.openvz_id, self.template ) )
			fd.write("vzctl set %s --devices c:10:200:rw  --capability net_admin:on --save\n" % self.openvz_id)
			if self.root_password:
				fd.write("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ) )
			fd.write("vzctl set %s --hostname %s --save\n" % ( self.openvz_id, self.name ) )
			for iface in self.interfaces_all():
				bridge = self.bridge_name(iface)
				fd.write("vzctl set %s --netif_add %s --save\n" % ( self.openvz_id, iface.name ) )
				fd.write("vzctl set %s --ifname %s --host_ifname veth%s.%s --bridge %s --save\n" % ( self.openvz_id, iface.name, self.openvz_id, iface.name, bridge ) )
		if script == "destroy":
			fd.write("vzctl destroy %s\n" % self.openvz_id)
			fd.write ( "true\n" )
		if script == "start":
			for iface in self.interfaces_all():
				bridge = self.bridge_name(iface)
				fd.write("brctl addbr %s\n" % bridge )
				fd.write("ip link set %s up\n" % bridge )
			fd.write("vzctl start %s --wait\n" % self.openvz_id)
			for iface in self.interfaces_all():
				if iface.is_configured():				
					ip4 = iface.configuredinterface.ip4address
					netmask = iface.configuredinterface.ip4netmask
					dhcp = iface.configuredinterface.use_dhcp
					if ip4:
						fd.write("vzctl exec %s ifconfig %s %s netmask %s up\n" % ( self.openvz_id, iface.name, ip4, netmask ) ) 
					if dhcp:
						fd.write("vzctl exec %s \"[ -e /sbin/dhclient ] && /sbin/dhclient %s\"\n" % ( self.openvz_id, iface.name ) )
						fd.write("vzctl exec %s \"[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s\"\n" % ( self.openvz_id, iface.name ) )					
			fd.write("( while true; do vncterm -rfbport %s -passwd %s -c vzctl enter %s ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid\n" % ( self.vnc_port, self.vnc_password(), self.openvz_id, self.name ) )
		if script == "stop":
			fd.write("cat vnc-%s.pid | xargs kill\n" % self.name )
			fd.write("vzctl stop %s\n" % self.openvz_id)
			fd.write ( "true\n" )

	def check_change_possible(self, newdev):
		if not self.template == newdev.template:
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Template of openvz vm %s cannot be changed" % self.name)
		if not self.host_name == newdev.host_name or not self.host_group == newdev.host_group:
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Host of openvz vm %s cannot be changed" % self.name)

	def change(self, newdev, fd):
		"""
		Adapt this device to the new device
		"""
		self.root_password = newdev.root_password
		self.host_group = newdev.host_group
		if self.root_password:
			fd.write("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ) )
		for iface in self.interfaces_all():
			fd.write("vzctl set %s --netif_del %s --save\n" % ( self.openvz_id, iface.name ) )
		self.interfaces = newdev.interfaces
		for iface in self.interfaces_all():
			bridge = self.bridge_name(iface)
			fd.write("vzctl set %s --netif_add %s --save\n" % ( self.openvz_id, iface.name ) )
			fd.write("vzctl set %s --ifname %s --host_ifname veth%s.%s --bridge %s --save\n" % ( self.openvz_id, iface.name, self.openvz_id, iface.name, bridge ) )

	def upload_image(self, filename, task):
		task.subtasks_total=4
		host = self.host
		tmp_id = uuid.uuid1()
		remote_filename= "/tmp/glabnetman-%s" % tmp_id
		dst = "root@%s:%s" % ( host.name, remote_filename )
		task.output.write(util.run_shell(["rsync",  "-a", filename, dst], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write(util.run_shell(["ssh",  "root@%s" % host.name, "vzctl", "remove", self.openvz_id ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write(util.run_shell(["ssh",  "root@%s" % host.name, "vzrestore", remote_filename, self.openvz_id ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write(util.run_shell(["ssh",  "root@%s" % host.name, "rm", remote_filename ], config.remote_dry_run))
		os.remove(filename)
		task.done()

	def download_image(self):
		host = self.host
		tmp_id = uuid.uuid1()
		filename = "/tmp/glabnetman-%s" % tmp_id
		src = "root@%s:%s/*.tgz" % ( host.name, filename )
		print util.run_shell(["ssh",  "root@%s" % host.name, "mkdir", "-p", filename ], config.remote_dry_run)
		print util.run_shell(["ssh",  "root@%s" % host.name, "vzdump", "--compress", "--dumpdir", filename, "--suspend", self.openvz_id ], config.remote_dry_run)
		print util.run_shell(["rsync",  "-a", src, filename], config.remote_dry_run)
		print util.run_shell(["ssh",  "root@%s" % host.name, "rm -r", filename ], config.remote_dry_run)
		return filename

class ConfiguredInterface(generic.Interface):
	use_dhcp = models.BooleanField()
	ip4address = models.CharField(max_length=15, null=True)
	ip4netmask = models.CharField(max_length=15, null=True)

	def init(self, device, dom):
		self.device = device
		self.decode_xml(dom)
		self.save()

	def encode_xml(self, dom, doc, internal):
		if self.use_dhcp:
			dom.setAttribute("use_dhcp", str(self.use_dhcp).lower())
		if self.ip4address:
			dom.setAttribute("ip4address", self.ip4address)
		if self.ip4netmask:
			dom.setAttribute("ip4netmask", self.ip4netmask)
		
	def decode_xml(self, dom):
		generic.Interface.decode_xml(self, dom)
		self.use_dhcp = util.parse_bool(util.get_attr(dom, "use_dhcp", default="false"))
		self.ip4address = util.get_attr(dom, "ip4address", default=None)
		self.ip4netmask = util.get_attr(dom, "ip4netmask", default=None)
		
	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass	