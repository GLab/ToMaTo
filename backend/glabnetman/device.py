# -*- coding: utf-8 -*-

from interface import *
from util import *
import host_store

class Device(XmlObject):
	"""
	This class represents a device
	"""
  
	def __init__ ( self, topology, dom, load_ids ):
		"""
		Creates a device object
		@param topology the parent topology object
		@param dom the xml dom object of the device
		@param load_ids whether to lod or ignore assigned ids
		"""
		self.interfaces={}
		self.topology = topology
		Device.decode_xml ( self, dom, load_ids )
		if not id:
			raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: device must have an id attribute")
		
	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	"""
	The id of the device in the topology. Must be unique inside a topology.
	"""

	type=property(curry(XmlObject.get_attr, "type"), curry(XmlObject.set_attr, "type"))
	"""
	The type of the device. Must be either "openvz" or "dhcpd"
	"""

	host_name=property(curry(XmlObject.get_attr, "host"), curry(XmlObject.set_attr, "host"))
	"""
	The name of the host of this device
	"""

	host_group=property(curry(XmlObject.get_attr, "hostgroup"), curry(XmlObject.set_attr, "hostgroup"))
	"""
	The name of the host of this device
	"""

	def decode_xml ( self, dom, load_ids ):
		"""
		Read the attributes from the xml dom object
		@param dom the xml dom object to read the data from
		@load_ids whether to load or ignore assigned ids
		"""
		if not load_ids:
			if dom.hasAttribute("host"):
				dom.removeAttribute("host")
		XmlObject.decode_xml(self,dom)
		for interface in dom.getElementsByTagName ( "interface" ):
			iface = Interface(self,interface, load_ids)
			self.interfaces[iface.id] = iface

	def encode_xml ( self, dom, doc, print_ids ):
		"""
		Encode the object to an xml dom object
		@param dom the xml dom object to write the data to
		@param doc the xml document needed to create child elements
		@print_ids whether to include or ignore assigned ids
		"""
		XmlObject.encode_xml(self,dom)
		if not print_ids:
			if dom.hasAttribute("host"):
				dom.removeAttribute("host")
		for interface in self.interfaces.values():
			iface = doc.createElement("interface")
			interface.encode_xml(iface,doc, print_ids)
			dom.appendChild(iface)

	def retake_resources(self):
		"""
		Take all resources that this object and child objects once had. Fields containing the ids of assigned resources control which resources will be taken.
		"""
		if self.host_name:
			self.host = host_store.get(self.host_name)
			self.host.devices.add(self)

	def take_resources(self):
		"""
		Take free resources for all unassigned resource slots of thos object and its child objects. The number of the resources will be stored in internal fields.
		"""
		if not self.host_name:
			self.host = host_store.select_host(self.host_group)
			self.host_name = self.host.name
			self.host.devices.add(self)

	def free_resources(self):
		"""
		Free all resources for all resource slots of this object and its child objects.
		"""
		self.host.devices.remove(self)
		self.host = None
		self.host_name = None
