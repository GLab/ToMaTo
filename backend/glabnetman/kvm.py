# -*- coding: utf-8 -*-

from django.db import models

import generic, hosts, fault, config, hashlib

def next_free_id (host):
	ids = range(1000,1100)
	for dev in KVMDevice.objects.filter(host=host):
		ids.remove(dev.kvm_id)
	return ids[0]

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
		self.kvm_id = next_free_id(self.host)
		self.vnc_port = hosts.next_free_port(self.host)
		self.save()		
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = generic.Interface()
			iface.init(self, interface)
			self.interfaces_add(iface)
	
	def download_image(self, filename, task):
		pass

	def upload_image(self, filename, task):
		pass

	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("template", self.template)
		if internal:
			dom.setAttribute("kvm_id", self.kvm_id)
		
	def decode_xml(self, dom):
		generic.Device.decode_xml(self, dom)
		self.template = dom.getAttribute("template")

	def bridge_name(self, interface):
		"""
		Returns the name of the bridge for the connection of the given interface
		Note: This must be 16 characters or less for brctl to work
		@param interface the interface
		"""
		if interface.connection:
			return interface.connection.bridge_name
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
			fd.write("qm create %s\n" % self.kvm_id )
			fd.write("mkdir -p /var/lib/vz/images/%s\n" % self.kvm_id)
			fd.write("cp /var/lib/vz/template/qemu/%s /var/lib/vz/images/%s\n" % (self.template, self.kvm_id))
			fd.write("qm set %s --ide0 local:%s/%s\n" % (self.kvm_id, self.kvm_id, self.template))
			for iface in self.interfaces_all():
				bridge = self.bridge_name(iface)
				fd.write("qm set %s --vlan%s e1000\n" % ( self.kvm_id, int(iface.id) ) )
		if script == "destroy":
			fd.write("qm destroy %s\n" % self.kvm_id)
			fd.write ( "true\n" )
		if script == "start":
			fd.write("qm start %s\n" % self.kvm_id)
			for iface in self.interfaces_all():
				bridge = self.bridge_name(iface)
				fd.write("brctl delif vmbr%s vmtab%si%s\n" % ( int(iface.id), self.kvm_id, int(iface.id) ) )
				fd.write("brctl addbr %s\n" % bridge )
				fd.write("brctl addif %s vmtab%si%s\n" % ( bridge, self.kvm_id, int(iface.id) ) )
				fd.write("ip link set %s up\n" % bridge )
			fd.write("( while true; do nc -l -p %s -c \"qm vncproxy %s %s 2>/dev/null\" ; done ) >/dev/null 2>&1 & echo $! > vnc-%s.pid\n" % ( self.vnc_port, self.kvm_id, self.vnc_password(), self.id ) )
		if script == "stop":
			fd.write("cat vnc-%s.pid | xargs kill\n" % self.id )
			fd.write("qm stop %s\n" % self.kvm_id)
			fd.write ( "true\n" )

	def check_change_possible(self, newdev):
		if not self.host_name == newdev.host_name or not self.host_group == newdev.host_group:
			raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Host of kvm vm %s cannot be changed" % self.id)

	def change(self, newdev, fd):
		"""
		Adapt this device to the new device
		"""
		raise fault.new(fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "KVM changes not supported yet")

	def vnc_password(self):
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.id))
		m.update(str(self.kvm_id))
		m.update(str(self.vnc_port))
		m.update(str(self.topology.owner))
		return m.hexdigest()
