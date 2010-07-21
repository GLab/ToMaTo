# -*- coding: utf-8 -*-

from xml.dom import minidom

from openvz_device import *
from dhcpd_device import *
from tinc_connector import *
from real_network_connector import *
from config import *
from resource_store import *

import shutil, os, stat

class Topology(XmlObject):
  
	def __init__ (self, file):
		self.devices={}
		self.connectors={}
		self.load_from(file)
		
	id=property(curry(XmlObject.get_attr, "id"), curry(XmlObject.set_attr, "id"))
	is_deployed=property(curry(XmlObject.get_attr, "is_deployed", res_type=bool, default=False), curry(XmlObject.set_attr, "is_deployed"))

	def add_device ( self, device ):
		device.topology = self
		self.devices[device.id] = device
		
	def add_connector ( self, connector ):
		connector.topology = self
		self.connectors[connector.id] = connector
		
	def load_from ( self, file ):
		dom = minidom.parse ( file )
		x_top = dom.getElementsByTagName ( "topology" )[0]
		XmlObject.decode_xml(self,x_top)
		for x_dev in x_top.getElementsByTagName ( "device" ):
			Type = { "openvz": OpenVZDevice, "dhcpd": DhcpdDevice }[x_dev.getAttribute("type")]
			self.add_device ( Type ( self, x_dev ) )
		for x_con in x_top.getElementsByTagName ( "connector" ):
			Type = { "hub": TincConnector, "switch": TincConnector, "router": TincConnector, "real": RealNetworkConnector }[x_con.getAttribute("type")]
			self.add_connector ( Type ( self, x_con ) )
			
	def create_dom ( self ):
		dom = minidom.Document()
		x_top = dom.createElement ( "topology" )
		XmlObject.encode_xml(self,x_top)
		dom.appendChild ( x_top )
		for dev in self.devices.values():
			x_dev = dom.createElement ( "device" )
			dev.encode_xml ( x_dev, dom )
			x_top.appendChild ( x_dev )
		for con in self.connectors.values():
			x_con = dom.createElement ( "connector" )
			con.encode_xml ( x_con, dom )
			x_top.appendChild ( x_con )
		return dom

	def save_to (self, file):
		dom = self.create_dom()
		fd = open ( file, "w" )
		dom.writexml(fd, indent="", addindent="\t", newl="\n")
		fd.close()

	def output (self):
		dom = self.create_dom()
		print dom.toprettyxml(indent="\t", newl="\n")

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

	def affected_hosts (self):
		hosts=set()
		for dev in self.devices.values():
			hosts.add(dev.host)
		return hosts

	def get_deploy_dir(self,host_name):
		return Config.local_deploy_dir+"/"+host_name

	def get_deploy_script(self,host_name,script):
		return self.get_deploy_dir(host_name)+"/"+script+".sh"

	def deploy(self):
		if not self.id:
			raise Exception("not registered")
		self.take_resources()
		self.write_deploy_scripts()
		self.upload_deploy_scripts()
		self.is_deployed = True
	
	def write_deploy_scripts(self):
		if not self.id:
			raise Exception("not registered")
		print "creating scripts ..."
		if Config.local_deploy_dir and os.path.exists(Config.local_deploy_dir):
			shutil.rmtree(Config.local_deploy_dir)
		for host in self.affected_hosts():
			dir=self.get_deploy_dir(host.name)
			if not os.path.exists(dir):
				os.makedirs(dir)
			for script in ("create", "destroy", "start", "stop"):
				script_fd = open(self.get_deploy_script(host.name,script), "w")
				script_fd.write("#!/bin/bash\n\n")
				script_fd.close()
				os.chmod(self.get_deploy_script(host.name,script), stat.S_IRWXU)
		for dev in self.devices.values():
			dev.write_deploy_script()
		for con in self.connectors.values():
			con.write_deploy_script()

	def upload_deploy_scripts(self):
		if not self.id:
			raise Exception("not registered")
		print "uploading scripts ..."
		for host in self.affected_hosts():
			print "\t%s ..." % host.name
			src = self.get_deploy_dir(host.name)
			dst = "root@%s:%s/%s" % ( host.name, Config.remote_deploy_dir, self.id )
			if bool(Config.remote_dry_run):
				print "DRY RUN: rsync -PAV %s %s" % ( src, dst )
			else:
				subprocess.check_call (["rsync",  "-Pav",  src, dst])
	
	def exec_script(self, script):
		if not self.id:
			raise Exception("not registered")
		if not self.is_deployed:
			raise Exception("not delpoyed")
		print "executing %s ..." % script
		script = "%s/%s/%s.sh" % ( Config.remote_deploy_dir, self.id, script )
		for host in self.affected_hosts():
			print "\t%s ..." % host.name
			if bool(Config.remote_dry_run):
				print "DRY RUN: ssh root@%s %s" % ( host.name, script )
			else:
				subprocess.check_call (["ssh",  "root@%s" % host.name, script ])

	def start(self):
		self.exec_script("start")

	def stop(self):
		self.exec_script("stop")

	def create(self):
		self.exec_script("create")

	def destroy(self):
		self.exec_script("destroy")
