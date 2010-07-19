# -*- coding: utf-8 -*-

from connector import *
from resource_store import *
from util import *
import os, subprocess, shutil

class TincConnector(Connector):

	def __init__(self, topology, dom ):
		Connector.__init__(self, topology, dom)
		for con in self.connections:
			con.port_number = None
			if "port_number" in con.attributes:
				con.port_number = con.attributes["port_number"]

	def take_resources(self):
		for con in self.connections:
			if not con.port_number:
				con.port_number = ResourceStore.host_ports[con.interface.device.host].take()
				con.attributes["port_number"] = str(con.port_number)

	def free_resources(self):
		for con in self.connections:
			ResourceStore.host_ports[con.interface.device.host].free(con.port_number)
			con.port_number = None
			del con.attributes["port_number"]

	def write_deploy_script(self, dir):
		print "# deploying tinc %s %s ..." % ( self.type, self.id )
		tincname = "tinc_" + self.topology.id + "." + self.id
		for con in self.connections:
			host = con.interface.device.host
			path = dir + "/" + host + "/" + tincname
			if not os.path.exists(path+"/hosts"):
				os.makedirs(path+"/hosts")
			subprocess.check_call (["openssl",  "genrsa",  "-out",  path + "/rsa_key.priv"])
			self_host_fd = open(path+"/hosts/"+host, "w")
			self_host_fd.write("Address=%s %s\n" % ( host, con.port_number ) )
			subprocess.check_call (["openssl",  "rsa", "-pubout", "-in",  path + "/rsa_key.priv", "-out",  path + "/hosts/" + host + ".pub"])
			self_host_pub_fd = open(path+"/hosts/"+host+".pub", "r")
			shutil.copyfileobj(self_host_pub_fd, self_host_fd)
			self_host_fd.close()
			self_host_pub_fd.close()
			tinc_conf_fd = open(path+"/tinc.conf", "w")
			tinc_conf_fd.write ( "Mode=%s\n" % self.type )
			tinc_conf_fd.write ( "Name=%s\n" % host )
			for con2 in self.connections:
				host2 = con2.interface.device.host
				if not host == host2:
					tinc_conf_fd.write ( "ConnectTo=%s\n" % host2 )
			tinc_conf_fd.close()
			startup_fd=open(dir+"/%s/startup.sh" % host, "a")
			startup_fd.write ( "ln -s $(pwd)/%s /etc/tincd/%s\n" % (tincname, tincname) )
			startup_fd.write ( "tincd --net=%s --chroot\n" % tincname )
			bridge_name=con.interface.device.bridge_name(con.interface)
			startup_fd.write ( "brctl addif %s %s\n" % (bridge_name, tincname ) )
			startup_fd.write ( "ip link set %s up\n" %  tincname )
			startup_fd.close ()
		for con in self.connections:
			host = con.interface.device.host
			path = dir + "/" + host + "/" + tincname
			for con2 in self.connections:
				host2 = con2.interface.device.host
				path2 = dir + "/" + host2 + "/" + tincname
				if not host == host2:
					shutil.copy(path+"/hosts/"+host, path2+"/hosts/"+host)
