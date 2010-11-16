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

import generic, hosts, fault, config, hashlib, re, util, uuid, os

class KVMDevice(generic.Device):
	kvm_id = models.IntegerField(null=True)
	template = models.CharField(max_length=30)
	vnc_port = models.IntegerField(null=True)
	
	def upcast(self):
		return self

	def get_state(self, task):
		if config.remote_dry_run:
			return self.state
		if not self.kvm_id:
			return generic.State.CREATED
		res = self.host.execute("qm status %s" % self.kvm_id, task)
		if "running" in res:
			return generic.State.STARTED
		if "stopped" in res:
			return generic.State.PREPARED
		if "unknown" in res:
			return generic.State.CREATED
		raise fault.new(fault.UNKNOWN, "Unable to determine kvm state for %s: %s" % ( self, res ) )

	def download_supported(self):
		return self.state == generic.State.PREPARED

	def download_image(self):
		tmp_id = uuid.uuid1()
		filename = "/tmp/glabnetman-%s" % tmp_id
		self.host.download("/var/lib/vz/images/%s/disk.qcow2" % self.kvm_id, filename)
		return filename

	def upload_supported(self):
		return self.state == generic.State.PREPARED

	def upload_image(self, filename, task):
		task.subtasks_total=1
		remote_filename= "/var/lib/vz/images/%s/disk.qcow2" % self.kvm_id
		self.host.upload(filename, remote_filename, task)
		task.subtasks_done = task.subtasks_done + 1
		os.remove(filename)
		task.done()

	def encode_xml(self, dom, doc, internal):
		generic.Device.encode_xml(self, dom, doc, internal)
		dom.setAttribute("template", self.template)
		if internal:
			if self.kvm_id:
				dom.setAttribute("kvm_id", str(self.kvm_id))
			if self.vnc_port:
				dom.setAttribute("vnc_port", str(self.vnc_port))
		
	def start_run(self, task):
		generic.Device.start_run(self, task)
		self.host.execute("qm start %s" % self.kvm_id, task)
		for iface in self.interfaces_all():
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			bridge = self.bridge_name(iface)
			self.host.bridge_create(bridge)
			self.host.bridge_connect(bridge, "vmtab%si%s" % ( self.kvm_id, iface_id ) )
			self.host.execute("ip link set %s up" % bridge, task)
		if not self.vnc_port:
			self.vnc_port = self.host.next_free_port()
			self.save()
		self.host.free_port(self.vnc_port, task)		
		self.host.execute("( while true; do nc -l -p %s -c \"qm vncproxy %s %s 2>/dev/null\" ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.vnc_port, self.kvm_id, self.vnc_password(), self.name ), task)
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.STARTED, "VM is not started"
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Device.stop_run(self, task)
		self.host.execute("cat vnc-%s.pid | xargs -r kill" % self.name, task)
		self.vnc_port=None
		self.host.execute("qm stop %s" % self.kvm_id, task)
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.PREPARED, "VM is not prepared"
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Device.prepare_run(self, task)
		self.template = hosts.get_template_name("kvm", self.template)
		if not self.host:
			self.host = hosts.get_best_host(self.hostgroup, self)
		if not self.kvm_id:
			self.kvm_id = self.host.next_free_vm_id()
			self.save()
		self.host.execute("qm create %s" % self.kvm_id, task)
		self.host.execute("mkdir -p /var/lib/vz/images/%s" % self.kvm_id, task)
		self.host.execute("cp /var/lib/vz/template/qemu/%s /var/lib/vz/images/%s/disk.qcow2" % (self.template, self.kvm_id), task)
		self.host.execute("qm set %s --ide0 local:%s/disk.qcow2" % (self.kvm_id, self.kvm_id), task)
		self.host.execute("qm set %s --name \"%s_%s\"" % (self.kvm_id, self.topology.name, self.name), task)
		for iface in self.interfaces_all():
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			self.host.bridge_create("vmbr%s" % iface_id)
			self.host.execute("qm set %s --vlan%s e1000" % ( self.kvm_id, iface_id ), task)
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
		self.host.execute("qm destroy %s" % self.kvm_id, task)
		self.state = self.get_state(task)
		assert self.state == generic.State.CREATED, "VM still exists"
		self.kvm_id=None
		self.host = None
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def configure(self, properties, task):
		generic.Device.configure(self, properties, task)
			
	def interfaces_add(self, name, properties, task):
		if self.state == "started":
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Changes of running KVMs are not supported")
		if not re.match("eth(\d+)", name):
			raise fault.new(fault.INVALID_INTERFACE_NAME, "Invalid interface name: %s" % name)
		iface = generic.Interface()
		try:
			if self.interfaces_get(name):
				raise fault.new(fault.DUPLICATE_INTERFACE_NAME, "Duplicate interface name: %s" % name)
		except:
			pass
		iface.name = name
		iface.device = self
		if self.state == "prepared":
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			self.host.bridge_create("vmbr%s" % iface_id)
			self.host.execute("qm set %s --vlan%s e1000\n" % ( self.kvm_id, iface_id ), task )
		iface.save()
		generic.Device.interfaces_add(self, iface)

	def interfaces_configure(self, name, properties, task):
		pass
	
	def interfaces_rename(self, name, properties, task):
		raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "KVM does not support renaming interfaces: %s" % name)
	
	def interfaces_delete(self, name, task):
		#FIXME: actually delete interface in VM
		iface = self.interfaces_get(name)
		iface.delete()
	
	def vnc_password(self):
		if not self.kvm_id:
			return "---"
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.name))
		m.update(str(self.kvm_id))
		m.update(str(self.vnc_port))
		m.update(str(self.topology.owner))
		return m.hexdigest()

	def get_resource_usage(self):
		if self.state == generic.State.CREATED:
			disk = 0
		else:
			disk = int(self.host.get_result("[ -s /var/lib/vz/images/%s/disk.qcow2 ] && stat -c %%s /var/lib/vz/images/%s/disk.qcow2 || echo 0" % (self.kvm_id, self.kvm_id)))
		if self.state == generic.State.STARTED:
			memory = int(self.host.get_result("[ -s /var/run/qemu-server/%s.pid ] && PROC=`cat /var/run/qemu-server/%s.pid` && [ -e /proc/$PROC/stat ] && cat /proc/$PROC/stat | awk '{print ($24 * 4096)}' || echo 0" % (self.kvm_id, self.kvm_id)))
			ports = 1
		else:
			memory = 0
			ports = 0
		return {"disk": disk, "memory": memory, "ports": ports, "public_ips": 0}		
