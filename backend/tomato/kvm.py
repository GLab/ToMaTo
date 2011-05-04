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

import generic, hosts, fault, config, hashlib, re, uuid, os

class KVMDevice(generic.Device):
	def upcast(self):
		return self

	def _qm(self, cmd, params=""):
		return self.host.execute("qm %s %s %s" % (cmd, self.attributes["vmid"], params))

	def _monitor(self, cmd):
		return self.host.execute("echo -e \"%(cmd)s\\n\" | socat - unix-connect:/var/run/qemu-server/%(vmid)s.mon; socat -u unix-connect:/var/run/qemu-server/%(vmid)s.mon - 2>&1 | dd count=0 2>/dev/null" % {"cmd": cmd, "vmid": self.attributes["vmid"]})

	def _image_path(self):
		return "/var/lib/vz/images/%s/disk.qcow2" % self.attributes["vmid"]

	def get_state(self):
		if config.remote_dry_run:
			return self.state
		if not self.attributes.get("vmid"):
			return generic.State.CREATED
		res = self._qm("status")
		if "running" in res:
			return generic.State.STARTED
		if "stopped" in res:
			return generic.State.PREPARED
		if "unknown" in res:
			return generic.State.CREATED
		raise fault.new(fault.UNKNOWN, "Unable to determine kvm state for %s: %s" % ( self, res ) )

	def download_supported(self):
		return self.state == generic.State.PREPARED

	def prepare_downloadable_image(self):
		filename = "%s_%s_%s.qcow2" % (self.topology.id, self.name, uuid.uuid1())
		path = "%s/%s" % (self.host.attributes["hostserver_basedir"], filename)
		self.host.file_copy(self._image_path(), path)
		self.host.file_chmod(path, 644)
		return filename

	def upload_supported(self):
		return self.state == generic.State.PREPARED

	def use_uploaded_image_run(self, path):
		self._qm("set", "--ide0 undef")
		self.host.file_move(path, self._image_path() )
		self.host.file_chown(self._image_path(), "root:root")
		self._qm("set", "--ide0=local:%s/disk.qcow2" % self.attributes["vmid"])
		self.attributes["template"] = "***custom***"
		self.save()

	def _start_vnc(self):
		if not self.attributes.get("vnc_port"):
			self.attributes["vnc_port"] = self.host.next_free_port()
			self.save()
		self.host.free_port(self.attributes["vnc_port"])		
		vmid = self.attributes["vmid"]
		self.host.execute("tcpserver -qHRl 0 0 %s qm vncproxy %s %s & echo $! > vnc-%s.pid" % ( self.attributes["vnc_port"], vmid, self.vnc_password(), self.name ))

	def _start_iface(self, iface):
		bridge = self.bridge_name(iface)
		self.host.bridge_create(bridge)
		self.host.bridge_connect(bridge, self.interface_device(iface) )
		self.host.execute("ip link set %s up" % bridge)		

	def _check_state(self, asserted):
		self.state = asserted #for dry-run
		self.state = self.get_state()
		self.save()
		assert self.state == asserted, "VM in wrong state"

	def get_start_tasks(self):
		import tasks
		taskset = generic.Device.get_start_tasks(self)
		taskset.addTask(tasks.Task("start-vm", self._qm, args=("start",)))
		taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.STARTED,), depends="start-vm"))
		for iface in self.interface_set_all():
			taskset.addTask(tasks.Task("start-interface-%s" % iface, self._start_iface, args=(iface,), depends="check-state"))
		taskset.addTask(tasks.Task("start-vnc", self._start_vnc, depends="check-state"))
		return taskset

	def _stop_vnc(self):
		self.host.process_kill("vnc-%s.pid" % self.name)
		self.host.free_port(self.attributes["vnc_port"])		
		del self.attributes["vnc_port"]
	
	def get_stop_tasks(self):
		import tasks
		taskset = generic.Device.get_stop_tasks(self)
		taskset.addTask(tasks.Task("stop-vm", self._qm, args=("stop",)))
		taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.PREPARED,), depends="stop-vm"))
		taskset.addTask(tasks.Task("stop-vnc", self._stop_vnc))
		return taskset

	def _assign_template(self):
		self.attributes["template"] = hosts.get_template_name("kvm", self.attributes.get("template"))
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
		self._qm("set", "--name \"%s_%s\"" % (self.topology.name, self.name))

	def _create_iface(self, iface):
		iface_id = re.match("eth(\d+)", iface.name).group(1)
		self.host.bridge_create("vmbr%s" % iface_id)
		self._qm("set", "--vlan%s e1000" % iface_id)			
	
	def get_prepare_tasks(self):
		import tasks
		taskset = generic.Device.get_prepare_tasks(self)
		taskset.addTask(tasks.Task("assign-template", self._assign_template))
		taskset.addTask(tasks.Task("assign-host", self._assign_host))		
		taskset.addTask(tasks.Task("assign-vmid", self._assign_vmid, depends="assign-host"))
		taskset.addTask(tasks.Task("create-vm", self._qm, args=("create",), depends="assign-vmid"))
		taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.PREPARED,), depends="create-vm"))
		taskset.addTask(tasks.Task("use-template", self._use_template, depends="check-state"))
		taskset.addTask(tasks.Task("configure-vm", self._configure_vm, depends="check-state"))
		for iface in self.interface_set_all():
			taskset.addTask(tasks.Task("create-interface-%s" % iface.name, self._create_iface, args=(iface,), depends="check-state"))
		return taskset

	def _unassign_host(self):
		self.host = None
		
	def _unassign_vmid(self):
		del self.attributes["vmid"]

	def get_destroy_tasks(self):
		import tasks
		taskset = generic.Device.get_destroy_tasks(self)
		if self.host:
			taskset.addTask(tasks.Task("destroy-vm", self._qm, args=("destroy",)))
			taskset.addTask(tasks.Task("check-state", self._check_state, args=(generic.State.CREATED,), depends="destroy-vm"))
			taskset.addTask(tasks.Task("unassign-host", self._unassign_host, depends="check-state"))
			taskset.addTask(tasks.Task("unassign-vmid", self._unassign_vmid, depends="check-state"))
		return taskset

	def configure(self, properties):
		if "template" in properties:
			assert self.state == generic.State.CREATED, "Cannot change template of prepared device: %s" % self.name
		generic.Device.configure(self, properties)
		if "template" in properties:
			self.attributes["template"] = hosts.get_template_name(self.type, properties["template"]) #pylint: disable-msg=W0201
			if not self.attributes["template"]:
				raise fault.new(fault.NO_SUCH_TEMPLATE, "Template not found:" % properties["template"])
		self.save()
			
	def interfaces_add(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		if self.state == "started":
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Changes of running KVMs are not supported")
		if not re.match("eth(\d+)", name):
			raise fault.new(fault.INVALID_INTERFACE_NAME, "Invalid interface name: %s" % name)
		iface = generic.Interface()
		try:
			if self.interface_set_get(name):
				raise fault.new(fault.DUPLICATE_INTERFACE_NAME, "Duplicate interface name: %s" % name)
		except generic.Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface.name = name
		iface.device = self
		if self.state == "prepared":
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			self.host.bridge_create("vmbr%s" % iface_id)
			self._qm("set", "--vlan%s e1000\n" % iface_id)
		iface.save()
		generic.Device.interface_set_add(self, iface)

	def interfaces_configure(self, name, properties):
		pass
	
	def interfaces_rename(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "KVM does not support renaming interfaces: %s" % name)
	
	def interfaces_delete(self, name): #@UnusedVariable, pylint: disable-msg=W0613
		if self.state == generic.State.STARTED:
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Changes of running KVMs are not supported")
		iface = self.interface_set_get(name)
		if self.state == generic.State.PREPARED:
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			self._qm("set", "--vlan%s undef\n" % iface_id)			
		iface.delete()
		
	def vnc_password(self):
		if not self.attributes["vmid"]:
			return "---"
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.name))
		m.update(str(self.attributes["vmid"]))
		m.update(str(self.attributes["vnc_port"]))
		m.update(str(self.topology.owner))
		return m.hexdigest()

	def get_resource_usage(self):
		if self.state == generic.State.CREATED:
			disk = 0
		else:
			try:
				disk = int(self.host.execute("[ -s /var/lib/vz/images/%(vmid)s/disk.qcow2 ] && stat -c %%s /var/lib/vz/images/%(vmid)s/disk.qcow2 || echo 0" % {"vmid": self.attributes["vmid"]}))
			except:
				disk = -1
		if self.state == generic.State.STARTED:
			try:
				memory = int(self.host.execute("[ -s /var/run/qemu-server/%(vmid)s.pid ] && PROC=`cat /var/run/qemu-server/%(vmid)s.pid` && [ -e /proc/$PROC/stat ] && cat /proc/$PROC/stat | awk '{print ($24 * 4096)}' || echo 0" % {"vmid": self.attributes["vmid"]}))
			except: #pylint: disable-msg=W0702
				memory = -1
			ports = 1
		else:
			memory = 0
			ports = 0
		return {"disk": disk, "memory": memory, "ports": ports}		
	
	def interface_device(self, iface):
		"""
		Returns the name of the host device for the given interface
		
		Note: Proxmox changes the names of the interface devices with every 
		release of qemu-server. Here the current list of naming schemes:
		qemu-server 1.1-22 vmtab1000i0 
		qemu-server 1.1-25 vmtab1000i0d0
		qemu-server 1.1-28 tap1000i0d0 or tap1000i0
		Due to this naming chaos the name must determined on the host with a
		command, so	this can only be determined for started devices.
		
		@param iface: interface object
		@type iface: generic.Interface
		@return: name of host device
		@rtype: string
		"""
		iface_id = re.match("eth(\d+)", iface.name).group(1)
		assert self.host, "Cannot determine KVM host device names when not running"
		#  not asserting state == started here, because this method will be used during start
		name = self.host.execute("(cd /sys/class/net; ls -d vmtab%(vmid)si%(iface_id)s vmtab%(vmid)si%(iface_id)sd0 tap%(vmid)si%(iface_id)s tap%(vmid)si%(iface_id)sd0 2>/dev/null)" % { "vmid": self.attributes["vmid"], "iface_id": iface_id }).strip()
		return name

	def _get_env(self):
		return {"host": self.host, "vmid": self.attributes["vmid"], "vnc_port": self.attributes["vnc_port"], "state": self.state}

	def _set_env(self, env):
		self.state = env["state"]
		self.host = env["host"]
		self.attributes["vmid"] = env["vmid"]
		self.attributes["vnc_port"] = env["vnc_port"]

	def migrate_run(self, host=None):
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
		disk = "%s/%s" % (self.host.attributes["hostserver_basedir"], self.prepare_downloadable_image())
		oldhost.file_move(disk, "%s/disk.qcow2" % tmp)
		oldhost.file_transfer("%s/disk.qcow2" % tmp, newhost, "%s/disk.qcow2" % tmp, direct=True)
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
			oldhost.execute("rdiff signature %(tmp)s/disk.qcow2 %(tmp)s/rdiff.sigs" % {"tmp": tmp})
			#create a memory snapshot on old host
			self._monitor("stop")
			self._monitor("savevm migrate")
			self.stop(True)
			#create and transfer a disk image rdiff
			disk2 = "%s/%s" % (self.host.attributes["hostserver_basedir"], self.prepare_downloadable_image())
			oldhost.execute("rdiff -- delta %s/rdiff.sigs %s - | gzip > %s/disk.rdiff.gz" % (tmp, disk2, tmp))
			oldhost.file_delete(disk2)
			oldhost.file_transfer("%s/disk.rdiff.gz" % tmp, newhost, "%s/disk.rdiff.gz" % tmp)
			#patch disk image with the rdiff
			newhost.execute("gunzip < %(tmp)s/disk.rdiff.gz | rdiff -- patch %(tmp)s/disk.qcow2 - %(tmp)s/disk-patched.qcow2" % {"tmp": tmp})
			newhost.file_move("%s/disk-patched.qcow2" % tmp, "%s/disk.qcow2" % tmp)			
		#destroy vm on old host
		self.destroy(True)
		oldenv = self._get_env()
		#use disk image on new host
		self._set_env(newenv)
		self.use_uploaded_image_run("%s/disk.qcow2" % tmp)
		if oldstate == generic.State.STARTED:
			self.start(True)
			# restore snapshot
			self._monitor("stop")
			self._monitor("loadvm migrate")
			self._monitor("cont")
			self._monitor("delvm migrate")
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

	#def migrate(self, host):
		#create new VM on new host
		#configure VM, interfaces etc.
		#if state >= prepared
			#rsync disk to a temp place on old host
			#move dist into hostserver
			#create download grant for new host and download
			#move disk image to VM area on new host
			#if state == started
				#connect to monitor (socat) and stop the vm
				#create a snapshot on old host
				#transfer the snapshot file to new host
				#create an rdiff of disk changes since rsync
				#transfer changes to new host
				#apply changes on new host
				#resume on new host
				#remove rdiff files
				#remove snapshot files  
			#remove disk images from hostserver
			#remove disk image in temp place
		#change vmid
		#change host
		#destroy on old host
		#redeploy all connected connectors
		#pass

	def to_dict(self, auth):
		res = generic.Device.to_dict(self, auth)
		if not auth:
			del res["attrs"]["vnc_port"]
		else:
			res["attrs"]["vnc_password"] = self.vnc_password()
		return res

