# -*- coding: utf-8 -*-

from device import Device
from util import curry, run_shell, parse_bool

import config, api

import os, uuid, hashlib

class KVMDevice(Device):
	"""
	This class represents a KVM device
	"""

	def __init__(self, topology, dom, load_ids):
		"""
		Creates a KVM device object
		@param topology the parent topology object
		@param dom the xml dom object of the device
		@param load_ids whether to lod or ignore assigned ids
		"""
		Device.__init__(self, topology, dom, load_ids)
		self.decode_xml(dom, load_ids)

	kvm_id=property(curry(Device.get_attr, "kvm_id"), curry(Device.set_attr, "kvm_id"))
	vnc_port=property(curry(Device.get_attr, "vnc_port"), curry(Device.set_attr, "vnc_port"))
	template=property(curry(Device.get_attr, "template", default=config.default_template), curry(Device.set_attr, "template"))
	
	def decode_xml ( self, dom, load_ids ):
		"""
		Read the attributes from the xml dom object
		@param dom the xml dom object to read the data from
		@param load_ids whether to load or ignore assigned ids
		"""
		if not load_ids:
			if dom.hasAttribute("kvm_id"):
				dom.removeAttribute("kvm_id")
			if dom.hasAttribute("vnc_port"):
				dom.removeAttribute("vnc_port")

	def encode_xml ( self, dom, doc, print_ids ):
		"""
		Encode the object to an xml dom object
		@param dom the xml dom object to write the data to
		@param doc the xml document needed to create child elements
		@param print_ids whether to include or ignore assigned ids
		"""
		Device.encode_xml(self,dom,doc,print_ids)
		if not print_ids:
			if dom.hasAttribute("kvm_id"):
				dom.removeAttribute("kvm_id")
			if dom.hasAttribute("vnc_port"):
				dom.removeAttribute("vnc_port")

	def retake_resources(self):
		"""
		Take all resources that this object and child objects once had. Fields containing the ids of assigned resources control which resources will be taken.
		"""
		Device.retake_resources(self)
		if self.kvm_id:
			self.host.kvm_ids.take_specific(self.kvm_id)
		if self.vnc_port:
			self.host.ports.take_specific(self.vnc_port)
	
	def take_resources(self):
		"""
		Take free resources for all unassigned resource slots of those object and its child objects. The number of the resources will be stored in internal fields.
		"""
		Device.take_resources(self)
		if not self.kvm_id:
			self.kvm_id=self.host.kvm_ids.take()
		if not self.vnc_port:
			self.vnc_port=self.host.ports.take()

	def free_resources(self):
		"""
		Free all resources for all resource slots of this object and its child objects.
		"""
		Device.free_resources(self)
		if self.kvm_id:
			self.host.kvm_ids.free(self.kvm_id)
			self.kvm_id=None
		if self.vnc_port:
			self.host.ports.free(self.vnc_port)
			self.vnc_port=None

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
			#TODO: add ide0
			for iface in self.interfaces.values():
				bridge = self.bridge_name(iface)
				fd.write("qm set %s --vlan%s e1000\n" % ( self.kvm_id, int(iface.id) ) )
		if script == "destroy":
			fd.write("qm destroy %s\n" % self.kvm_id)
			fd.write ( "true\n" )
		if script == "start":
			fd.write("qm start %s\n" % self.kvm_id)
			for iface in self.interfaces.values():
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
			raise api.Fault(api.Fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "Host of kvm vm %s cannot be changed" % self.id)

	def change(self, newdev, fd):
		"""
		Adapt this device to the new device
		"""
		raise api.Fault(api.Fault.IMPOSSIBLE_TOPOLOGY_CHANGE, "KVM changes not supported yet")

	def vnc_password(self):
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(self.id)
		m.update(self.kvm_id)
		m.update(self.vnc_port)
		m.update(str(self.topology.owner))
		return m.hexdigest()

	def __str__(self):
		return "kvm %s" % self.id
