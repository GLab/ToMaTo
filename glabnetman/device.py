# -*- coding: utf-8 -*-

from interface import *
from util import *
from host_store import *

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
		try:
			self.host = HostStore.get(self.host_name)
		except KeyError:
			raise Exception("Unknown host: %s" % self.host_name)
		
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

	def decode_xml ( self, dom, load_ids ):
		"""
		Read the attributes from the xml dom object
		@param dom the xml dom object to read the data from
		@load_ids whether to load or ignore assigned ids
		"""
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
		for interface in self.interfaces.values():
			iface = doc.createElement("interface")
			interface.encode_xml(iface,doc, print_ids)
			dom.appendChild(iface)
