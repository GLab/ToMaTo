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

import generic, util, hosts, hashlib, config, fault, os, uuid

class OpenVZDevice(generic.Device):
	openvz_id = models.IntegerField(null=True)
	root_password = models.CharField(max_length=50, null=True)
	template = models.CharField(max_length=30)
	vnc_port = models.IntegerField(null=True)
	gateway = models.CharField(max_length=15, null=True)
		
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
		
	"""
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")
		self.root_password = dom.getAttribute("root_password")
		self.gateway = util.get_attr(dom, "gateway", default=None)
	"""

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
		self.host.execute("timeout 10 vzctl start %s --wait" % self.openvz_id, task)
		for iface in self.interfaces_all():
			if iface.is_configured():
				iface = iface.upcast()
				iface.start_run(task)
				assert config.remote_dry_run or self.host.interface_bridge(iface.interface_name()) == self.bridge_name(iface), "Interface %s not connected to bridge %s" % (iface.interface_name(), self.bridge_name(iface))
		if self.gateway:
			self.host.execute("vzctl exec %s route add default gw %s" % ( self.openvz_id, self.gateway), task) 
		if not self.vnc_port:
			self.vnc_port = self.host.next_free_port()
			self.save()		
		self.host.free_port(self.vnc_port, task)		
		self.host.execute("( while true; do vncterm -rfbport %s -passwd %s -c vzctl enter %s ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.vnc_port, self.vnc_password(), self.openvz_id, self.name ), task)
		self.state = generic.State.STARTED #for dry-run
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.STARTED, "VM is not running"
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Device.stop_run(self, task)
		self.host.execute("cat vnc-%s.pid | xargs -r kill" % self.name, task)
		self.vnc_port=None
		self.host.execute("vzctl stop %s" % self.openvz_id, task)
		self.state = generic.State.PREPARED #for dry-run
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Device.prepare_run(self, task)
		self.template = hosts.get_template_name("openvz", self.template)
		if not self.host:
			self.host = hosts.get_best_host(self.hostgroup, self)
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
		self.state = generic.State.PREPARED #for dry-run
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Device.destroy_run(self, task)
		if self.openvz_id:
			self.host.execute("vzctl destroy %s" % self.openvz_id, task)
		self.state = generic.State.CREATED #for dry-run
		self.state = self.get_state(task)
		assert self.state == generic.State.CREATED, "VM still exists"
		self.openvz_id=None
		self.host = None
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def configure(self, properties, task):
		generic.Device.configure(self, properties, task)
		if "root_password" in properties:
			self.root_password = properties["root_password"]
			if self.state == "prepared" or self.state == "started":
				self.host.execute("vzctl set %s --userpasswd root:%s --save\n" % ( self.openvz_id, self.root_password ), task )
		if "gateway" in properties:
			self.gateway = properties["gateway"]
			if self.gateway and self.state == "started":
				self.host.execute("vzctl exec %s route add default gw %s" % ( self.openvz_id, self.gateway), task)
		self.save()

	def interfaces_add(self, name, properties, task):
		if self.state == generic.State.STARTED:
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "OpenVZ does not support adding interfaces to running VMs: %s" % self.name)
		import re
		if not re.match("eth(\d+)", name):
			raise fault.new(fault.INVALID_INTERFACE_NAME, "Invalid interface name: %s" % name)
		try:
			if self.interfaces_get(name):
				raise fault.new(fault.DUPLICATE_INTERFACE_NAME, "Duplicate interface name: %s" % name)
		except:
			pass
		iface = ConfiguredInterface()
		iface.name = name
		iface.device = self
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			iface.prepare_run(task)
		iface.configure(properties, task)
		iface.save()
		generic.Device.interfaces_add(self, iface)

	def interfaces_configure(self, name, properties, task):
		iface = self.interfaces_get(name).upcast()
		iface.configure(properties, task)

	def interfaces_rename(self, name, properties, task):
		iface = self.interfaces_get(name).upcast()
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			self.host.execute("vzctl set %s --netif_del %s --save\n" % ( self.openvz_id, iface.name ), task )
		try:
			if self.interfaces_get(properties["name"]):
				raise fault.new(fault.DUPLICATE_INTERFACE_NAME, "Duplicate interface name: %s" % properties["name"])
		except:
			pass
		iface.name = properties["name"]
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			iface.prepare_run(task)
		if self.state == generic.State.STARTED:
			iface.start_run(task)	
		iface.save()

	def interfaces_delete(self, name, task):
		iface = self.interfaces_get(name).upcast()
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			self.host.execute("vzctl set %s --netif_del %s --save\n" % ( self.openvz_id, iface.name ), task )
		iface.delete()

	def upload_supported(self):
		return self.state == generic.State.PREPARED

	def upload_image(self, filename, task):
		task.subtasks_total=2
		tmp_id = uuid.uuid1()
		remote_filename= "/tmp/tomato-%s" % tmp_id
		self.host.upload(filename, remote_filename, task)
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("rm -rf /var/lib/vz/private/%s" % self.openvz_id, task)
		self.host.execute("mkdir /var/lib/vz/private/%s" % self.openvz_id, task)
		self.host.execute("tar -xzf %s -C /var/lib/vz/private/%s" % ( remote_filename, self.openvz_id ), task)
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("rm %s" % remote_filename, task)
		os.remove(filename)
		self.template = "***custom***"
		self.save()
		task.done()

	def download_supported(self):
		return self.state == generic.State.PREPARED

	def download_image(self):
		tmp_id = uuid.uuid1()
		filename = "/tmp/tomato-%s" % tmp_id
		self.host.execute("tar --numeric-owner -czf %s -C /var/lib/vz/private/%s . " % ( filename, self.openvz_id ) )
		self.host.download("%s" % filename, filename)
		self.host.execute("rm %s" % filename)
		return filename
	
	def get_resource_usage(self):
		if self.state == generic.State.CREATED:
			disk = 0
		elif self.state == generic.State.STARTED:
			disk = int(self.host.get_result("grep -h -A 1 -E '^%s:' /proc/vz/vzquota | tail -n 1 | awk '{print $2}'" % self.openvz_id))*1024
		else:
			try:
				disk = int(self.host.get_result("du -sb /var/lib/vz/private/%s | awk '{print $1}'" % self.openvz_id))
			except:
				disk = 0
		if self.state == generic.State.STARTED:
			memory = int(self.host.get_result("grep -e '^[ ]*%s:' -A 20 /proc/user_beancounters | fgrep privvmpages | awk '{print $2}'" % self.openvz_id))*4*1024
			ports = 1
		else:
			memory = 0
			ports = 0
		return {"disk": disk, "memory": memory, "ports": ports}		

	def interface_device(self, iface):
		return "veth%s.%s" % ( self.upcast().openvz_id, iface.name )


class ConfiguredInterface(generic.Interface):
	use_dhcp = models.BooleanField()
	ip4address = models.CharField(max_length=18, null=True)

	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Interface.encode_xml(self, dom, doc, internal)
		if self.use_dhcp:
			dom.setAttribute("use_dhcp", str(self.use_dhcp).lower())
		if self.ip4address:
			dom.setAttribute("ip4address", self.ip4address)

	def interface_name(self):
		return self.device.upcast().interface_device(self)
		
	def configure(self, properties, task):
		changed=False
		if "use_dhcp" in properties:
			self.use_dhcp = util.parse_bool(properties["use_dhcp"])
			changed = True
		if "ip4address" in properties:
			self.ip4address = properties["ip4address"]
			changed = True
		if changed:
			if self.device.state == generic.State.STARTED:
				self.start_run(task)
			self.save()
			
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