# -*- coding: utf-8 -*-

from django.db import models

import dummynet, generic

class TincConnector(generic.Connector):
	
	def __init__(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		for connection in dom.getElementsByTagName ( "connection" ):
			self.connection_set.add ( TincConnection(self, connection) )
	
	def encode_xml(self, dom, doc, internal):
		pass
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)

class TincConnection(dummynet.EmulatedConnection):
	tinc_id = models.IntegerField()
	
	def __init__(self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
	
	def encode_xml(self, dom, doc, internal):
		if internal:
			dom.setAttribute("tinc_id", self.tinc_id)
		
	def decode_xml(self, dom):
		dummynet.EmulatedConnection.decode_xml(self, dom)