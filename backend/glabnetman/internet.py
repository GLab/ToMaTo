# -*- coding: utf-8 -*-

from django.db import models

import generic

class InternetConnector(generic.Connector):

	def __init__(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		for connection in dom.getElementsByTagName ( "connection" ):
			self.connection_set.add ( generic.Connection(self, connection) )

	def encode_xml(self, dom, doc, internal):
		pass
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)