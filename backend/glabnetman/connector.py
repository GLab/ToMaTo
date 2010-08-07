# -*- coding: utf-8 -*-

from connection import *
from util import *

class Connector(XmlObject):
	"""
	This class represents a connector
	"""
  
	def __init__ ( self, topology, dom, load_ids ):
		"""
		Creates a connector object
		@param topology the parent topology object
		@param dom the xml dom object of the connector
		@param load_ids whether to lod or ignore assigned ids
		"""
		self.connections=set()
		self.topology = topology
		Connector.decode_xml ( self, dom, load_ids )
		if not id:
			raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: connector must have an id attribute")

	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	"""
	The id of the connector in the topology. Must be unique inside a topology.
	"""
	
	type=property(curry(XmlObject.get_attr, "type"), curry(XmlObject.set_attr, "type"))
	"""
	The type of the connector. Must be either "real", "hub", "switch" or "router"
	"""
	
	def decode_xml ( self, dom, load_ids ):
		"""
		Read the attributes from the xml dom object
		@param dom the xml dom object to read the data from
		@load_ids whether to load or ignore assigned ids
		"""
		XmlObject.decode_xml(self,dom)
		for connection in dom.getElementsByTagName ( "connection" ):
			self.connections.add ( Connection(self, connection, load_ids) )

	def encode_xml ( self, dom, doc, print_ids ):
		"""
		Encode the object to an xml dom object
		@param dom the xml dom object to write the data to
		@param doc the xml document needed to create child elements
		@print_ids whether to include or ignore assigned ids
		"""
		XmlObject.encode_xml(self,dom)
		for con in self.connections:
			x_con = doc.createElement("connection")
			con.encode_xml (x_con, doc, print_ids)
			dom.appendChild(x_con)
