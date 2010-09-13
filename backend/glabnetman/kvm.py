# -*- coding: utf-8 -*-

from django.db import models

import generic, hosts, fault, config, hashlib, re, util, uuid, os

class KVMDevice(generic.Device):
	kvm_id = models.IntegerField(null=True)
	template = models.CharField(max_length=30)
	vnc_port = models.IntegerField(null=True)
	
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.template = hosts.get_template("kvm", self.template)
		if not self.template:
			raise fault.new(fault.NO_SUCH_TEMPLATE, "Template not found for %s" % self)
		self.host = hosts.get_best_host(self.hostgroup)
		self.save()		
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = generic.Interface()
			iface.init(self, interface)
			self.interfaces_add(iface)
	
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
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")

	def start_run(self, task):
		generic.Device.start_run(self, task)
		self.host.execute("qm start %s" % self.kvm_id, task)
		for iface in self.interfaces_all():
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			bridge = self.bridge_name(iface)
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
		self.host.execute("qm destroy %s" % self.kvm_id, task)
		self.kvm_id=None
		self.state = self.get_state(task)
		self.save()
		assert self.state == generic.State.CREATED, "VM still exists"
		task.subtasks_done = task.subtasks_done + 1

	def is_changed(self, dom):
		if not self.template == util.get_attr(dom, "template", self.template):
			return True
		old_ifaces = [i.name for i in self.interfaces_all()]
		new_ifaces = [i.getAttribute("id") for i in dom.getElementsByTagName("interface")]
		return not old_ifaces == new_ifaces

	def change_possible(self, dom):
		generic.Device.change_possible(self, dom)
		if not self.template == util.get_attr(dom, "template", self.template):
			if self.state == "started" or self.state == "prepared":
				raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Template of kvm %s cannot be changed" % self.name)
		if self.is_changed(dom) and self.state == "started":
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Changes of running KVMs are not supported")

	def change_run(self, dom, task):
		"""
		Adapt this device to the new device
		"""
		generic.Device.change_run(self, dom, task)
		self.template = util.get_attr(dom, "template", self.template)
		ifaces=set()
		for x_iface in dom.getElementsByTagName("interface"):
			name = x_iface.getAttribute("id")
			ifaces.add(name)
			try:
				iface = self.interfaces_get(name)
			except generic.Interface.DoesNotExist:
				#new interface
				iface = generic.Interface()
				iface.init(self, x_iface)
				self.interfaces_add(iface)
				if self.state == "prepared":
					iface_id = re.match("eth(\d+)", iface.name).group(1)
					self.host.bridge_create("vmbr%s" % iface_id)
					self.host.execute("qm set %s --vlan%s e1000\n" % ( self.kvm_id, iface_id ), task )
		for iface in self.interfaces_all():
			if not iface.name in ifaces:
				#deleted interface
				if self.state == "prepared":
					iface_id = re.match("eth(\d+)", iface.name).group(1)
					#FIXME: find a way to delete interfaces
				iface.delete()
		self.save()
		

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
