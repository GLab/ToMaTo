# -*- coding: utf-8 -*-

from xml.dom import minidom

from openvz_device import *
from dhcpd_device import *
from hub_connector import *
from switch_connector import *
from router_connector import *
from config import *

class Topology:
  
	def __init__ (self, file):
		self.devices={}
		self.connectors={}
		self.load_from(file)
		
	def add_device ( self, device ):
		device.topology = self
		self.devices[device.id] = device
		
	def add_connector ( self, connector ):
		connector.topology = self
		self.connectors[connector.id] = connector
		
	def load_from ( self, file ):
		dom = minidom.parse ( file )
		x_top = dom.getElementsByTagName ( "topology" )[0]
		self.id = x_top.getAttribute("id")
		for x_dev in x_top.getElementsByTagName ( "device" ):
			Type = { "openvz": OpenVZDevice, "dhcpd": DhcpdDevice }[x_dev.getAttribute("type")]
			self.add_device ( Type ( self, x_dev ) )
		for x_con in x_top.getElementsByTagName ( "connector" ):
			Type = { "hub": HubConnector, "switch": SwitchConnector, "router": RouterConnector }[x_con.getAttribute("type")]
			self.add_connector ( Type ( self, x_con ) )
			
	def save_to ( self, file ):
		pass

	def deploy(self):
		self.write_deploy_scripts()
		self.upload_deploy_scripts()
	
	def write_deploy_scripts(self):
		for dev in self.devices.values():
			dev.write_deploy_script(Config.deploy_dir)
		for con in self.connectors.values():
			con.write_deploy_script(Config.deploy_dir)
	
	def upload_deploy_scripts(self):
		pass
	
	def output(self):
		for device in self.devices.values():
			print "Device %s on host %s type %s" % ( device.id, device.host, device.type )
			for interface in device.interfaces.values():
				print "\t Interface %s" % interface.id
		for connector in self.connectors.values():
			print "Connector %s type %s" % ( connector.id, connector.type )
			for interface in connector.connections:
				print "\t Interface %s.%s" % ( interface.device.id, interface.id )
