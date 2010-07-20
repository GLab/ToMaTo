# -*- coding: utf-8 -*-

from xml.dom import minidom

from openvz_device import *
from dhcpd_device import *
from tinc_connector import *
from config import *

class Topology(object):
  
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
		if x_top.hasAttribute("id"):
			self.id = x_top.getAttribute("id")
		else:
			self.id = str(ResourceStore.topology_ids.take())
		for x_dev in x_top.getElementsByTagName ( "device" ):
			Type = { "openvz": OpenVZDevice, "dhcpd": DhcpdDevice }[x_dev.getAttribute("type")]
			self.add_device ( Type ( self, x_dev ) )
		for x_con in x_top.getElementsByTagName ( "connector" ):
			self.add_connector ( TincConnector ( self, x_con ) )
			
	def save_to ( self, file ):
		dom = minidom.Document()
		x_top = dom.createElement ( "topology" )
		x_top.setAttribute("id", str(self.id))
		dom.appendChild ( x_top )
		for dev in self.devices.values():
			x_dev = dom.createElement ( "device" )
			dev.encode_xml ( x_dev, dom )
			x_top.appendChild ( x_dev )
		for con in self.connectors.values():
			x_con = dom.createElement ( "connector" )
			con.encode_xml ( x_con, dom )
			x_top.appendChild ( x_con )
		fd = open ( file, "w" )
		dom.writexml(fd, indent="", addindent="\t", newl="\n", encoding="")
		fd.close()

	def take_resources ( self ):
		for dev in self.devices.values():
			dev.take_resources()
		for con in self.connectors.values():
			con.take_resources()

	def free_resources ( self ):
		for dev in self.devices.values():
			dev.free_resources()
		for con in self.connectors.values():
			con.free_resources()

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
			for connection in connector.connections:
				print "\t Interface %s.%s" % ( connection.interface.device.id, connection.interface.id )
