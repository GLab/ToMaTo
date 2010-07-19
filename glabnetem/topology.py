# -*- coding: utf-8 -*-

from openvz_device import *
from dhcpd_device import *
from hub_connector import *
from switch_connector import *
from router_connector import *

class Topology:
  
	def __init__ (self, dom):
		self.devices={}
		self.connectors={}
		self.decode_xml(dom)
		
	def add_device ( self, device ):
		device.topology = self
		self.devices[device.id] = device
		
	def add_connector ( self, connector ):
		connector.topology = self
		self.connectors[connector.id] = connector
		
	def decode_xml ( self, dom ):
		x_top = dom.getElementsByTagName ( "topology" )[0]
		self.id = x_top.getAttribute("id")
		for x_dev in x_top.getElementsByTagName ( "device" ):
			Type = { "openvz": OpenVZDevice, "dhcpd": DhcpdDevice }[x_dev.getAttribute("type")]
			self.add_device ( Type ( self, x_dev ) )
		for x_con in x_top.getElementsByTagName ( "connector" ):
			Type = { "hub": HubConnector, "switch": SwitchConnector, "router": RouterConnector }[x_con.getAttribute("type")]
			self.add_connector ( Type ( self, x_con ) )
			
	def deploy(self, dir):
		for dev in self.devices.values():
			dev.deploy(dir)
		for con in self.connectors.values():
			con.deploy(dir)
				
	def output(self):
		for device in self.devices.values():
			print "Device %s on host %s type %s" % ( device.id, device.host, device.type )
			for interface in device.interfaces.values():
				print "\t Interface %s" % interface.id
		for connector in self.connectors.values():
			print "Connector %s type %s" % ( connector.id, connector.type )
			for interface in connector.connections:
				print "\t Interface %s.%s" % ( interface.device.id, interface.id )
