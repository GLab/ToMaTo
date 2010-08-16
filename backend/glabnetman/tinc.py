# -*- coding: utf-8 -*-

from django.db import models

import dummynet, generic, hosts

def next_free_id (host):
	ids = range(1,100)
	for con in TincConnection.objects.filter(interface__device__host=host):
		ids.remove(con.tinc_id)
	return ids[0]

class TincConnector(generic.Connector):
	
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.save()
		for connection in dom.getElementsByTagName ( "connection" ):
			con = TincConnection()
			con.init(self, connection)
			self.connection_set.add ( con )
	
	def encode_xml(self, dom, doc, internal):
		pass
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)

	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass


class TincConnection(dummynet.EmulatedConnection):
	tinc_id = models.IntegerField()
	
	def init(self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
		self.bridge_id = hosts.next_free_bridge(self.interface.device.host)
		self.tinc_id = next_free_id(self.interface.device.host)
		self.save()
	
	def encode_xml(self, dom, doc, internal):
		if internal:
			dom.setAttribute("tinc_id", self.tinc_id)
		
	def decode_xml(self, dom):
		dummynet.EmulatedConnection.decode_xml(self, dom)
		
	def write_aux_files(self):
		#TODO
		pass
	
	def write_control_script(self, host, script, fd):
		#TODO
		pass
		