# -*- coding: utf-8 -*-

from django.db import models

import generic, hosts, fault, config, hashlib, re, util, uuid, os

class KVMDevice(generic.Device):
	kvm_id = models.IntegerField()
	template = models.CharField(max_length=30)
	vnc_port = models.IntegerField()
	
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		if not self.template:
			self.template = config.kvm_default_template
		self.host = hosts.get_best_host(self.hostgroup)
		self.kvm_id = self.host.next_free_vm_id()
		self.vnc_port = self.host.next_free_port()
		self.save()		
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = generic.Interface()
			iface.init(self, interface)
			self.interfaces_add(iface)
	
	def upcast(self):
		return self

	def download_supported(self):
		return self.state == generic.State.PREPARED or self.state == generic.State.STARTED

	def download_image(self):
		tmp_id = uuid.uuid1()
		filename = "/tmp/glabnetman-%s" % tmp_id
		self.host.execute("mkdir -p %s" % filename)
		self.host.execute("vzdump --compress --dumpdir %s --suspend %s " % ( filename, self.kvm_id ) )
		self.host.download("%s/*.tgz" % filename, filename)
		self.host.execute("rm -r %s" % filename)
		return filename

	def upload_supported(self):
		return self.state == generic.State.CREATED or self.state == generic.State.PREPARED

	def upload_image(self, filename, task):
		task.subtasks_total=4
		tmp_id = uuid.uuid1()
		remote_filename= "/tmp/glabnetman-%s" % tmp_id
		self.host.upload(filename, remote_filename, task)
		task.subtasks_done = task.subtasks_done + 1
		if self.state == generic.State.PREPARED:
			self.host.execute("qm destroy %s" % self.kvm_id, task)
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("qmrestore %s %s" % ( remote_filename, self.kvm_id ), task)
		self.state = generic.State.PREPARED
		task.subtasks_done = task.subtasks_done + 1
		self.host.execute("rm %s" % remote_filename, task)
		os.remove(filename)
		task.done()

	def encode_xml(self, dom, doc, internal):
		generic.Device.encode_xml(self, dom, doc, internal)
		dom.setAttribute("template", self.template)
		if internal:
			dom.setAttribute("kvm_id", self.kvm_id)
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")

	def start_run(self, task):
		generic.Device.start_run(self, task)
		self.host.execute("qm start %s" % self.kvm_id, task)
		for iface in self.interfaces_all():
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			bridge = self.bridge_name(iface)
			self.host.execute("brctl delif vmbr%s vmtab%si%s" % ( iface_id, self.kvm_id, iface_id ), task)
			self.host.execute("brctl addbr %s" % bridge, task)
			self.host.execute("brctl addif %s vmtab%si%s" % ( bridge, self.kvm_id, iface_id ), task)
			self.host.execute("ip link set %s up" % bridge, task)
		self.host.execute("( while true; do nc -l -p %s -c \"qm vncproxy %s %s 2>/dev/null\" ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid" % ( self.vnc_port, self.kvm_id, self.vnc_password(), self.name ), task)
		self.state = generic.State.STARTED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Device.stop_run(self, task)
		self.host.execute("cat vnc-%s.pid | xargs kill" % self.name, task)
		self.host.execute("qm stop %s" % self.kvm_id, task)
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Device.prepare_run(self, task)
		self.host.execute("qm create %s" % self.kvm_id, task)
		self.host.execute("mkdir -p /var/lib/vz/images/%s" % self.kvm_id, task)
		self.host.execute("cp /var/lib/vz/template/qemu/%s /var/lib/vz/images/%s" % (self.template, self.kvm_id), task)
		self.host.execute("qm set %s --ide0 local:%s/%s" % (self.kvm_id, self.kvm_id, self.template), task)
		self.host.execute("qm set %s --name \"%s_%s\"" % (self.kvm_id, self.topology.name, self.name), task)
		for iface in self.interfaces_all():
			iface_id = re.match("eth(\d+)", iface.name).group(1)
			self.host.execute("qm set %s --vlan%s e1000" % ( self.kvm_id, iface_id ), task)
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Device.destroy_run(self, task)
		self.host.execute("qm destroy %s" % self.kvm_id, task)
		self.state = generic.State.CREATED
		self.save()
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
					self.host.execute("qm set %s --vlan%s e1000\n" % ( self.kvm_id, iface_id ) )
		for iface in self.interfaces_all():
			if not iface.name in ifaces:
				#deleted interface
				if self.state == "prepared":
					iface_id = re.match("eth(\d+)", iface.name).group(1)
					#FIXME: find a way to delete interfaces
				iface.delete()
		

	def vnc_password(self):
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.name))
		m.update(str(self.kvm_id))
		m.update(str(self.vnc_port))
		m.update(str(self.topology.owner))
		return m.hexdigest()
