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

	def _vzctl(self, cmd, params=""):
		return self.host.execute("vzctl %s %s %s" % (cmd, self.attributes["vmid"], params) )

	def _exec(self, cmd):
		return self._vzctl("exec", cmd)

	def _image_path(self):
		return "/var/lib/vz/private/%s" % self.attributes["vmid"]

	def execute(self, cmd):
		if self.state == generic.State.STARTED:
			return self._exec(cmd)
		else:
			raise fault.new(fault.INVALID_TOPOLOGY_STATE, "Device must be running to execute commands on it: %s" % self.name)

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
	
	def _start_vnc(self):
		if not self.attributes.get("vnc_port"):
			self.attributes["vnc_port"] = self.host.next_free_port()
			self.save()		
		self.host.free_port(self.attributes["vnc_port"])		
		self.host.execute("( while true; do vncterm -rfbport %s -passwd %s -c vzctl enter %s ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.attributes["vnc_port"], self.vnc_password(), self.attributes["vmid"], self.name ))

	def _wait_until_started(self):
		self._exec("while fgrep -q boot /proc/1/cmdline; do sleep 1; done")
	
	def _check_state(self, asserted):
		self.state = asserted #for dry-run
		self.state = self.get_state()
		self.save()
		assert self.state == asserted, "VM in wrong state"

	def _create_bridges(self):
		for iface in self.interface_set_all():
			if iface.is_connected():
				bridge = self.bridge_name(iface)
				assert bridge, "Interface has no bridge %s" % iface
				self.host.bridge_create(bridge)
				self.host.execute("ip link set %s up" % bridge)

	def _configure_routes(self):
		if self.attributes.get("gateway4"):
			self._exec("ip route add default via %s" % self.attributes["gateway4"]) 
		if self.attributes.get("gateway6"):
			self._exec("ip route add default via %s" % self.attributes["gateway6"]) 

	def get_start_tasks(self):
		import tasks
		taskset = generic.Device.get_start_tasks(self)
		taskset.addTask(tasks.Task("create-bridges", self._create_bridges))
		taskset.addTask(tasks.Task("start-vm", self._vzctl, args=("start",), depends="create-bridges"))
		taskset.addTask(tasks.Task("wait-start", self._wait_until_started, depends="start-vm"))
		taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.STARTED,), depends="wait-start"))
		for iface in self.interface_set_all():
			taskset.addTaskSet("interface-%s" % iface.name, iface.upcast().get_start_tasks().addGlobalDepends("check-state"))
		taskset.addTask(tasks.Task("configure-routes", self._configure_routes, depends="check-state"))
		taskset.addTask(tasks.Task("start-vnc", self._start_vnc, depends="check-state"))
		return taskset

	def _stop_vnc(self):
		self.host.process_kill("vnc-%s.pid" % self.name)
		self.host.free_port(self.attributes["vnc_port"])		
		del self.attributes["vnc_port"]

	def get_stop_tasks(self):
		import tasks
		taskset = generic.Device.get_stop_tasks(self)
		taskset.addTask(tasks.Task("stop-vnc", self._stop_vnc))
		taskset.addTask(tasks.Task("stop-vm", self._vzctl, args=("stop",)))
		taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.PREPARED,), depends="stop-vm"))
		return taskset	

	def _assign_template(self):
		self.attributes["template"] = hosts.get_template_name("openvz", self.attributes.get("template"))
		assert self.attributes["template"] and self.attributes["template"] != "None", "Template not found"

	def _assign_host(self):
		if not self.host:
			self.host = self.host_options().best()
			assert self.host, "No matching host found"
			self.save()

	def _assign_vmid(self):
		if not self.attributes.get("vmid"):
			self.attributes["vmid"] = self.host.next_free_vm_id()

	def _use_template(self):
		vmid = self.attributes["vmid"]
		self.host.file_mkdir("/var/lib/vz/images/%s" % vmid)
		self.host.file_copy("/var/lib/vz/template/qemu/%s.qcow2" % self.attributes["template"], self._image_path())
		self._qm("set", "--ide0 local:%s/disk.qcow2" % vmid)

	def _configure_vm(self):
		self._vzctl("set", "--devices c:10:200:rw --capability net_admin:on --save")
		if self.attributes.get("root_password"):
			self._vzctl("set", "--userpasswd root:%s --save" % self.attributes["root_password"])
		self._vzctl("set", "--hostname %s-%s --save" % (self.topology.name.replace("_","-"), self.name ))

	def get_prepare_tasks(self):
		import tasks
		taskset = generic.Device.get_prepare_tasks(self)
		taskset.addTask(tasks.Task("assign-template", self._assign_template))
		taskset.addTask(tasks.Task("assign-host", self._assign_host))		
		taskset.addTask(tasks.Task("assign-vmid", self._assign_vmid, depends="assign-host"))
		taskset.addTask(tasks.Task("create-vm", self._vzctl, args=("create","--ostemplate %s" % self.attributes["template"]), depends="assign-vmid"))
		taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.PREPARED,), depends="create-vm"))
		taskset.addTask(tasks.Task("configure-vm", self._configure_vm, depends="check-state"))
		for iface in self.interface_set_all():
			taskset.addTaskSet("interface-%s" % iface.name, iface.upcast().get_prepare_tasks().addGlobalDepends("check-state"))
		return taskset

	def _unassign_host(self):
		self.host = None
		
	def _unassign_vmid(self):
		del self.attributes["vmid"]

	def get_destroy_tasks(self):
		import tasks
		taskset = generic.Device.get_destroy_tasks(self)
		if self.host:
			taskset.addTask(tasks.Task("destroy-vm", self._vzctl, args=("destroy",)))
			taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.CREATED,), depends="destroy-vm"))
			taskset.addTask(tasks.Task("unassign-host", self._unassign_host, depends="check-state"))
			taskset.addTask(tasks.Task("unassign-vmid", self._unassign_vmid, depends="check-state"))
		return taskset

	def configure(self, properties):
		if "template" in properties:
			assert self.state == generic.State.CREATED, "Cannot change template of prepared device: %s" % self.name
		generic.Device.configure(self, properties)
		if "root_password" in properties:
			if self.state == "prepared" or self.state == "started":
				self._vzctl("set", "--userpasswd root:%s --save\n" % self.attributes["root_password"])
		if "gateway4" in properties:
			if self.attributes["gateway4"] and self.state == "started":
				self._exec("ip route add default via %s" % self.attributes["gateway4"])
		if "gateway6" in properties:
			if self.attributes["gateway6"] and self.state == "started":
				self._exec("ip route add default via %s" % self.attributes["gateway6"])
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

	def _get_env(self):
		return {"host": self.host, "vmid": self.attributes["vmid"], "vnc_port": self.attributes["vnc_port"], "state": self.state}

	def _set_env(self, env):
		self.state = env["state"]
		self.host = env["host"]
		self.attributes["vmid"] = env["vmid"]
		self.attributes["vnc_port"] = env["vnc_port"]

	def migrate_run(self, host=None):
		#FIXME: both vmids must be reserved the whole time
		if self.state == generic.State.CREATED:
			self.host = None
			self.save()
			return
		if not host:
			host = self.host_options().best()
		if not host:
			raise fault.new(fault.NO_HOSTS_AVAILABLE, "No matching host found")
		#save old data
		oldhost = self.host
		oldenv = self._get_env()
		oldstate = self.state
		#save new data
		newhost = host
		newvmid = newhost.next_free_vm_id()
		newenv = {"host": newhost, "state": generic.State.CREATED, "vmid": newvmid, "vnc_port": None}
		#prepare new vm
		self._set_env(newenv)
		self.prepare(True)
		newenv = self._get_env()
		#create a tmp directory on both hosts
		tmp = "/tmp/%s" % uuid.uuid1()
		oldhost.file_mkdir(tmp)
		newhost.file_mkdir(tmp)
		#transfer vm disk image
		self._set_env(oldenv)
		targz = "%s/%s" % (self.host.attributes["hostserver_basedir"], self.prepare_downloadable_image())
		oldhost.file_move(targz, "%s/disk.tar.gz" % tmp)
		oldhost.file_transfer("%s/disk.tar.gz" % tmp, newhost, "%s/disk.tar.gz" % tmp, direct=True)
		newhost.execute("gunzip < %s/disk.tar.gz > %s/disk.tar" % (tmp, tmp))
		#stop all connectors
		constates={}
		for iface in self.interface_set_all():
			if iface.is_connected():
				con = iface.connection.connector
				if con.name in constates:
					continue
				constates[con.name] = con.state
				if con.state == generic.State.STARTED:
					con.stop(True)
				if con.state == generic.State.PREPARED:
					con.destroy(True)		
		if oldstate == generic.State.STARTED:
			#prepare rdiff before snapshot to save time
			oldhost.execute("gunzip < %(tmp)s/disk.tar.gz > %(tmp)s/disk.tar" % {"tmp": tmp})
			oldhost.execute("rdiff signature %(tmp)s/disk.tar %(tmp)s/rdiff.sigs" % {"tmp": tmp})
			#create a memory snapshot on old host and transfer it
			self._stop_vnc()
			import time
			time.sleep(10)
			self._vzctl("chkpnt", "--dumpfile %s/openvz.dump" % tmp)
			self.state = generic.State.PREPARED
			oldhost.file_transfer("%s/openvz.dump" % tmp, newhost, "%s/openvz.dump" % tmp, direct=True)
			#create and transfer a disk image rdiff
			targz2 = "%s/%s" % (self.host.attributes["hostserver_basedir"], self.prepare_downloadable_image(gzip=False))
			oldhost.execute("rdiff -- delta %s/rdiff.sigs %s - | gzip > %s/disk.rdiff.gz" % (tmp, targz2, tmp))
			oldhost.file_delete(targz2)
			oldhost.file_transfer("%s/disk.rdiff.gz" % tmp, newhost, "%s/disk.rdiff.gz" % tmp)
			#patch disk image with the rdiff
			newhost.execute("gunzip < %(tmp)s/disk.rdiff.gz | rdiff -- patch %(tmp)s/disk.tar - %(tmp)s/disk-patched.tar" % {"tmp": tmp})
			newhost.file_move("%s/disk-patched.tar" % tmp, "%s/disk.tar" % tmp)
		#destroy vm on old host
		self.destroy(True)
		oldenv = self._get_env()
		#use disk image on new host
		self._set_env(newenv)
		self.use_uploaded_image_run("%s/disk.tar" % tmp, gzip=False)
		if oldstate == generic.State.STARTED:
			#restore memory snapshot on new host
			self._vzctl("restore", "--dumpfile %s/openvz.dump" % tmp)
			assert self.get_state() == generic.State.STARTED 
			self._start_vnc()
			self.state = generic.State.STARTED
		#remove tmp directories
		oldhost.file_delete(tmp, recursive=True)
		newhost.file_delete(tmp, recursive=True)
		#save changes
		self.save()
		#redeploy all connectors
		for iface in self.interface_set_all():
			if iface.is_connected():
				con = iface.connection.connector
				if not con.name in constates:
					continue
				state = constates[con.name]
				del constates[con.name]
				if state == generic.State.PREPARED or state == generic.State.STARTED:
					con.prepare(True)
				if state == generic.State.STARTED:
					con.start(True)


	def upload_supported(self):
		return self.state == generic.State.PREPARED

	def use_uploaded_image_run(self, path, gzip=True):
		self.host.file_delete(self._image_path(), recursive=True)
		self.host.file_mkdir(self._image_path())
		self.host.execute("tar -x%sf %s -C %s" % ( "z" if gzip else "", path, self._image_path() ))
		self.host.file_delete(path)
		self.attributes["template"] = "***custom***"
		self.save()

	def download_supported(self):
		return self.state == generic.State.PREPARED

	def prepare_downloadable_image(self, gzip=True):
		filename = "%s_%s_%s.tar%s" % (self.topology.id, self.name, uuid.uuid1(), ".gz" if gzip else "")
		path = "%s/%s" % (self.host.attributes["hostserver_basedir"], filename)
		self.host.execute("tar --numeric-owner -c%sf %s -C %s . " % ( "z" if gzip else "", path, self._image_path() ) )
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

	def _connect_to_bridge(self):
		dev = self.device.upcast()
		bridge = dev.bridge_name(self)
		if self.is_connected():
			dev.host.bridge_connect(bridge, self.interface_name())
			dev.host.execute("ip link set %s up" % bridge)
			
	def _configure_network(self):
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
			
	def get_start_tasks(self):
		import tasks
		taskset = generic.Interface.get_start_tasks(self)
		taskset.addTask(tasks.Task("connect-to-bridge", self._connect_to_bridge))
		taskset.addTask(tasks.Task("configure-network", self._configure_network, depends="connect-to-bridge"))
		return taskset

	def _create_interface(self):
		dev = self.device.upcast()
		dev._vzctl("set", "--netif_add %s --save" % self.name)
		dev._vzctl("set", "--ifname %s --host_ifname %s --save" % ( self.name, self.interface_name()))
		
	def get_prepare_tasks(self):
		import tasks
		taskset = generic.Interface.get_prepare_tasks(self)
		taskset.addTask(tasks.Task("create-interface", self._create_interface))
		return taskset

	def to_dict(self, auth):
		res = generic.Interface.to_dict(self, auth)		
		return res				