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

	def get_state(self, task):
		if config.remote_dry_run:
			return self.state
		if not self.attributes.get("vmid"):
			return generic.State.CREATED
		res = self.host.execute("qm status %s" % self.attributes["vmid"], task)
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
		self.host.execute("cp /var/lib/vz/images/%(vmid)s/disk.qcow2 %(path)s; chmod 644 %(path)s" % {"vmid": self.attributes["vmid"], "path": path})
		return filename

	def upload_supported(self):
		return self.state == generic.State.PREPARED

	def use_uploaded_image_run(self, filename, task):
		task.subtasks_total=2
		path = "%s/%s" % (self.attributes["hostserver_basedir"], filename)
		vmid = self.attributes["vmid"]
		dst = "/var/lib/vz/images/%s/disk.qcow2" % vmid
		self.host.execute("qm set %s --ide0 undef" % vmid, task)
		self.host.execute("mv %s %s" % ( path, dst ), task)
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("chown root:root %s" % dst, task)
		self.host.execute("qm set %(vmid)s --ide0=local:%(vmid)s/disk.qcow2" % {"vmid": vmid}, task)
		task.subtasks_done = task.subtasks_done + 1
		self.attributes["template"] = "***custom***"
		self.save()
		task.done()

	def start_run(self, task):
		generic.Device.start_run(self, task)
		vmid = self.attributes["vmid"]
		self.host.execute("qm start %s" % vmid, task)
		for iface in self.interface_set_all():
			bridge = self.bridge_name(iface)
			self.host.bridge_create(bridge)
			self.host.bridge_connect(bridge, self.interface_device(iface) )
			self.host.execute("ip link set %s up" % bridge, task)
		if not self.attributes.get("vnc_port"):
			self.attributes["vnc_port"] = self.host.next_free_port()
			self.save()
		self.host.free_port(self.attributes["vnc_port"], task)		
		self.host.execute("( while true; do nc -l -p %s -c \"qm vncproxy %s %s 2>/dev/null\" ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.attributes["vnc_port"], vmid, self.vnc_password(), self.name ), task)
		self.state = generic.State.STARTED #for dry-run
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.STARTED, "VM is not started"
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Device.stop_run(self, task)
		self.host.execute("cat vnc-%s.pid | xargs -r kill" % self.name, task)
		del self.attributes["vnc_port"]
		self.host.execute("qm stop %s" % self.attributes["vmid"], task)
		self.state = generic.State.PREPARED #for dry-run
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Device.prepare_run(self, task)
		self.attributes["template"] = hosts.get_template_name("kvm", self.attributes.get("template"))
		if not self.host:
			self.host = self.host_options().best()
			if not self.host:
				raise fault.new(fault.NO_HOSTS_AVAILABLE, "No matching host found")
		if not self.attributes.get("vmid"):
			self.attributes["vmid"] = self.host.next_free_vm_id()
			self.save()
		vmid = self.attributes["vmid"]
		self.host.execute("qm create %s" % vmid, task)
		self.host.execute("mkdir -p /var/lib/vz/images/%s" % vmid, task)
		self.host.execute("cp /var/lib/vz/template/qemu/%s /var/lib/vz/images/%s/disk.qcow2" % (self.attributes["template"], vmid), task)
		self.host.execute("qm set %(vmid)s --ide0 local:%(vmid)s/disk.qcow2" % {"vmid": vmid}, task)
		self.host.execute("qm set %s --name \"%s_%s\"" % (vmid, self.topology.name, self.name), task)
		for iface in self.interface_set_all():
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			self.host.bridge_create("vmbr%s" % iface_id)
			self.host.execute("qm set %s --vlan%s e1000" % ( vmid, iface_id ), task)
		self.state = generic.State.PREPARED #for dry-run
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Device.destroy_run(self, task)
		if not self.host:
			self.state = self.get_state(task)
			self.save()
			return
		self.host.execute("qm destroy %s" % self.attributes["vmid"], task)
		self.state = generic.State.CREATED #for dry-run
		self.state = self.get_state(task)
		assert self.state == generic.State.CREATED, "VM still exists"
		del self.attributes["vmid"]
		self.host = None
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def configure(self, properties, task):
		if "template" in properties:
			assert self.state == generic.State.CREATED, "Cannot change template of prepared device: %s" % self.name
		generic.Device.configure(self, properties, task)
		if "template" in properties:
			self.attributes["template"] = hosts.get_template_name(self.type, properties["template"]) #pylint: disable-msg=W0201
			if not self.attributes["template"]:
				raise fault.new(fault.NO_SUCH_TEMPLATE, "Template not found:" % properties["template"])
		self.save()
			
	def interfaces_add(self, name, properties, task): #@UnusedVariable, pylint: disable-msg=W0613
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
			self.host.execute("qm set %s --vlan%s e1000\n" % ( self.attributes["vmid"], iface_id ), task )
		iface.save()
		generic.Device.interface_set_add(self, iface)

	def interfaces_configure(self, name, properties, task):
		pass
	
	def interfaces_rename(self, name, properties, task): #@UnusedVariable, pylint: disable-msg=W0613
		raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "KVM does not support renaming interfaces: %s" % name)
	
	def interfaces_delete(self, name, task): #@UnusedVariable, pylint: disable-msg=W0613
		if self.state == generic.State.STARTED:
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Changes of running KVMs are not supported")
		iface = self.interface_set_get(name)
		if self.state == generic.State.PREPARED:
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			self.host.execute("qm set %s --vlan%s undef\n" % ( self.attributes["vmid"], iface_id ), task )			
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
				disk = int(self.host.get_result("[ -s /var/lib/vz/images/%(vmid)s/disk.qcow2 ] && stat -c %%s /var/lib/vz/images/%(vmid)s/disk.qcow2 || echo 0" % {"vmid": self.attributes["vmid"]}))
			except:
				disk = 0
		if self.state == generic.State.STARTED:
			try:
				memory = int(self.host.get_result("[ -s /var/run/qemu-server/%(vmid)s.pid ] && PROC=`cat /var/run/qemu-server/%(vmid)s.pid` && [ -e /proc/$PROC/stat ] && cat /proc/$PROC/stat | awk '{print ($24 * 4096)}' || echo 0" % {"vmid": self.attributes["vmid"]}))
			except: #pylint: disable-msg=W0702
				memory = 0
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
		name = self.host.get_result("(cd /sys/class/net; ls -d vmtab%(vmid)si%(iface_id)s vmtab%(vmid)si%(iface_id)sd0 tap%(vmid)si%(iface_id)s tap%(vmid)si%(iface_id)sd0 2>/dev/null)" % { "vmid": self.attributes["vmid"], "iface_id": iface_id }).strip()
		return name

	def to_dict(self, auth):
		res = generic.Device.to_dict(self, auth)
		if not auth:
			del res["attrs"]["vnc_port"]
			del res["attrs"]["vnc_password"]
		return res

