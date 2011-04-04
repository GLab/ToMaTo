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
	def upcast(self):
		return self

	def _vzctl(self, cmd, params="", timeout=None):
		return self.host.execute("%svzctl %s %s %s" % ("timeout %s " % timeout if timeout else "", cmd, self.attributes["vmid"], params) )

	def _exec(self, cmd):
		return self._vzctl("exec", cmd)

	def _image_path(self):
		return "/var/lib/vz/private/%s" % self.attributes["vmid"]

	def vnc_password(self):
		if not self.attributes.get("vnc_port"):
			return None 
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.name))
		m.update(str(self.attributes["vmid"]))
		m.update(str(self.attributes["vnc_port"]))
		m.update(str(self.topology.owner))
		return m.hexdigest()
	
	def get_state(self):
		if config.remote_dry_run:
			return self.state
		if not self.attributes["vmid"]:
			return generic.State.CREATED
		res = self._vzctl("status")
		if "exist" in res and "running" in res:
			return generic.State.STARTED
		if "exist" in res and "down" in res:
			return generic.State.PREPARED
		if "deleted" in res:
			return generic.State.CREATED
		raise fault.new(fault.UNKNOWN, "Unable to determine openvz state for %s: %s" % ( self, res ) )
	
	def start_run(self):
		generic.Device.start_run(self)
		for iface in self.interface_set_all():
			if iface.is_connected():
				bridge = self.bridge_name(iface)
				assert bridge, "Interface has no bridge %s" % iface
				self.host.bridge_create(bridge)
				self.host.execute("ip link set %s up" % bridge)
		self._vzctl("start", "--wait", timeout=10)
		for iface in self.interface_set_all():
			if iface.is_configured():
				iface = iface.upcast()
				iface.start_run()
				assert config.remote_dry_run or self.host.interface_bridge(iface.interface_name()) == self.bridge_name(iface), "Interface %s not connected to bridge %s" % (iface.interface_name(), self.bridge_name(iface))
		if self.attributes.get("gateway"):
			self._exec("ip route add default via %s" % self.attributes["gateway"]) 
		if not self.attributes.get("vnc_port"):
			self.attributes["vnc_port"] = self.host.next_free_port()
			self.save()		
		self.host.free_port(self.attributes["vnc_port"])		
		self.host.execute("( while true; do vncterm -rfbport %s -passwd %s -c vzctl enter %s ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.attributes["vnc_port"], self.vnc_password(), self.attributes["vmid"], self.name ))
		self.state = generic.State.STARTED #for dry-run
		self.state = self.get_state()
		self.save()
		assert self.state == generic.State.STARTED, "VM is not running"

	def stop_run(self):
		generic.Device.stop_run(self)
		self.host.process_kill("vnc-%s.pid" % self.name)
		del self.attributes["vnc_port"]
		self._vzctl("stop")
		self.state = generic.State.PREPARED #for dry-run
		self.state = self.get_state()
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"

	def prepare_run(self):
		generic.Device.prepare_run(self)
		self.attributes["template"] = hosts.get_template_name("openvz", self.attributes.get("template"))
		if not self.host:
			self.host = self.host_options().best()
			if not self.host:
				raise fault.new(fault.NO_HOSTS_AVAILABLE, "No matching host found")
		if not self.attributes.get("vmid"):
			self.attributes["vmid"] = self.host.next_free_vm_id()
			self.save()
		self._vzctl("create", "--ostemplate %s" % self.attributes["template"])
		self._vzctl("set", "--devices c:10:200:rw --capability net_admin:on --save")
		if self.attributes.get("root_password"):
			self._vzctl("set", "--userpasswd root:%s --save" % self.attributes["root_password"])
		self._vzctl("set", "--hostname %s-%s --save" % (self.topology.name.replace("_","-"), self.name ))
		for iface in self.interface_set_all():
			iface.upcast().prepare_run()
		self.state = generic.State.PREPARED #for dry-run
		self.state = self.get_state()
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"

	def destroy_run(self):
		generic.Device.destroy_run(self)
		if self.attributes.get("vmid"):
			self._vzctl("destroy")
		self.state = generic.State.CREATED #for dry-run
		self.state = self.get_state()
		assert self.state == generic.State.CREATED, "VM still exists"
		del self.attributes["vmid"]
		self.host = None
		self.save()

	def configure(self, properties):
		if "template" in properties:
			assert self.state == generic.State.CREATED, "Cannot change template of prepared device: %s" % self.name
		generic.Device.configure(self, properties)
		if "root_password" in properties:
			if self.state == "prepared" or self.state == "started":
				self._vzctl("set", "--userpasswd root:%s --save\n" % self.attributes["root_password"])
		if "gateway" in properties:
			if self.attributes["gateway"] and self.state == "started":
				self._exec("route add default gw %s" % self.attributes["gateway"])
		if "template" in properties:
			self.attributes["template"] = hosts.get_template_name(self.type, properties["template"]) #pylint: disable-msg=W0201
			if not self.attributes["template"]:
				raise fault.new(fault.NO_SUCH_TEMPLATE, "Template not found: %s" % properties["template"])
		self.save()

	def interfaces_add(self, name, properties):
		if self.state == generic.State.STARTED:
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "OpenVZ does not support adding interfaces to running VMs: %s" % self.name)
		import re
		if not re.match("eth(\d+)", name):
			raise fault.new(fault.INVALID_INTERFACE_NAME, "Invalid interface name: %s" % name)
		try:
			if self.interface_set_get(name):
				raise fault.new(fault.DUPLICATE_INTERFACE_NAME, "Duplicate interface name: %s" % name)
		except generic.Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface = ConfiguredInterface()
		iface.name = name
		iface.device = self
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			iface.prepare_run()
		iface.configure(properties)
		iface.save()
		generic.Device.interface_set_add(self, iface)

	def interfaces_configure(self, name, properties):
		iface = self.interface_set_get(name).upcast()
		iface.configure(properties)

	def interfaces_rename(self, name, properties):
		iface = self.interface_set_get(name).upcast()
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			self._vzctl("set", "--netif_del %s --save\n" % iface.name)
		try:
			if self.interface_set_get(properties["name"]):
				raise fault.new(fault.DUPLICATE_INTERFACE_NAME, "Duplicate interface name: %s" % properties["name"])
		except generic.Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface.name = properties["name"]
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			iface.prepare_run()
		if self.state == generic.State.STARTED:
			iface.start_run()	
		iface.save()

	def interfaces_delete(self, name):
		iface = self.interface_set_get(name).upcast()
		if self.state == generic.State.PREPARED or self.state == generic.State.STARTED:
			self._vzctl("set", "--netif_del %s --save\n" % iface.name)
		iface.delete()

	def upload_supported(self):
		return self.state == generic.State.PREPARED

	def use_uploaded_image_run(self, filename):
		path = "%s/%s" % (self.host.attributes["hostserver_basedir"], filename)
		self.host.file_delete(self._image_path(), recursive=True)
		self.host.file_mkdir(self._image_path())
		self.host.execute("tar -xzf %s -C %s" % ( path, self._image_path() ))
		self.host.file_delete(path)
		self.attributes["template"] = "***custom***"
		self.save()

	def download_supported(self):
		return self.state == generic.State.PREPARED

	def prepare_downloadable_image(self):
		filename = "%s_%s_%s.tar.gz" % (self.topology.id, self.name, uuid.uuid1())
		path = "%s/%s" % (self.host.attributes["hostserver_basedir"], filename)
		self.host.execute("tar --numeric-owner -czf %s -C %s . " % ( path, self._image_path() ) )
		return filename
	
	def get_resource_usage(self):
		if self.state == generic.State.CREATED:
			disk = 0
		elif self.state == generic.State.STARTED:
			try:
				disk = int(self.host.execute("grep -h -A 1 -E '^%s:' /proc/vz/vzquota | tail -n 1 | awk '{print $2}'" % self.attributes["vmid"]))*1024
			except:
				disk = -1
		else:
			try:
				disk = int(self.host.execute("du -sb %s | awk '{print $1}'" % self._image_path()))
			except: #pylint: disable-msg=W0702
				disk = -1
		if self.state == generic.State.STARTED:
			try:
				memory = int(self.host.execute("grep -e '^[ ]*%s:' -A 20 /proc/user_beancounters | fgrep privvmpages | awk '{print $2}'" % self.attributes["vmid"]))*4*1024
			except:
				memory = -1
			ports = 1
		else:
			memory = 0
			ports = 0
		return {"disk": disk, "memory": memory, "ports": ports}		

	def interface_device(self, iface):
		return "veth%s.%s" % ( self.attributes["vmid"], iface.name )

	def to_dict(self, auth):
		res = generic.Device.to_dict(self, auth)
		if not auth:
			del res["attrs"]["vnc_port"]
			del	res["attrs"]["root_password"]
		else:
			res["attrs"]["vnc_password"] = self.vnc_password()
		return res

class ConfiguredInterface(generic.Interface):
	def upcast(self):
		return self

	def interface_name(self):
		return self.device.upcast().interface_device(self)
		
	def configure(self, properties):
		generic.Interface.configure(self, properties)
		changed=False
		if "use_dhcp" in properties:
			changed = True
		if "ip4address" in properties:
			changed = True
		if "ip6address" in properties:
			changed = True
		if changed:
			if self.device.state == generic.State.STARTED:
				self.start_run()
			self.save()
			
	def start_run(self):
		bridge = self.device.upcast().bridge_name(self)
		if self.is_connected():
			self.device.host.bridge_connect(bridge, self.interface_name())
		dev = self.device.upcast()
		if self.attributes["ip4address"]:
			dev._exec("ip addr add %s dev %s" % ( self.attributes["ip4address"], self.name )) 
			dev._exec("ip link set up dev %s" % self.name ) 
		if self.attributes["ip6address"]:
			dev._exec("ip addr add %s dev %s" % ( self.attributes["ip6address"], self.name )) 
			dev._exec("ip link set up dev %s" % self.name ) 
		if self.attributes["use_dhcp"] and util.parse_bool(self.attributes["use_dhcp"]):
			dev._exec("\"[ -e /sbin/dhclient ] && /sbin/dhclient %s\"" % self.name)
			dev._exec("\"[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s\"" % self.name)
		if self.is_connected():					
			dev.host.execute("ip link set %s up" % bridge)

	def prepare_run(self):
		dev = self.device.upcast()
		dev._vzctl("set", "--netif_add %s --save" % self.name)
		dev._vzctl("set", "--ifname %s --host_ifname %s --save" % ( self.name, self.interface_name()))
		
	def to_dict(self, auth):
		res = generic.Interface.to_dict(self, auth)		
		return res				