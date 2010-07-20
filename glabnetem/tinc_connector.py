# -*- coding: utf-8 -*-

from connector import *
from resource_store import *
from host_store import *
from util import *
import os, subprocess, shutil

class TincConnector(Connector):

	def __init__(self, topology, dom ):
		Connector.__init__(self, topology, dom)
		Connection.port_number = property(curry(Connection.get_attr, "port_number"), curry(Connection.set_attr, "port_number"))

	def take_resources(self):
		for con in self.connections:
			if not con.port_number:
				con.port_number = str(con.interface.device.host.ports.take())

	def free_resources(self):
		for con in self.connections:
			con.interface.device.host.ports.free(con.port_number)
			con.port_number = None

	def write_deploy_script(self):
		print "\tcreating scripts for tinc %s %s ..." % ( self.type, self.id )
		tincname = "tinc_" + self.topology.id + "." + self.id
		for con in self.connections:
			host = con.interface.device.host
			path = self.topology.get_deploy_dir(host.name) + "/" + tincname
			if not os.path.exists(path+"/hosts"):
				os.makedirs(path+"/hosts")
			subprocess.check_call (["openssl",  "genrsa",  "-out",  path + "/rsa_key.priv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			self_host_fd = open(path+"/hosts/"+host.name, "w")
			self_host_fd.write("Address=%s %s\n" % ( host.name, con.port_number ) )
			subprocess.check_call (["openssl",  "rsa", "-pubout", "-in",  path + "/rsa_key.priv", "-out",  path + "/hosts/" + host.name + ".pub"], stderr=subprocess.PIPE)
			self_host_pub_fd = open(path+"/hosts/"+host.name+".pub", "r")
			shutil.copyfileobj(self_host_pub_fd, self_host_fd)
			self_host_fd.close()
			self_host_pub_fd.close()
			tinc_conf_fd = open(path+"/tinc.conf", "w")
			tinc_conf_fd.write ( "Mode=%s\n" % self.type )
			tinc_conf_fd.write ( "Name=%s\n" % host.name )
			for con2 in self.connections:
				host2 = con2.interface.device.host
				if not host.name == host2.name:
					tinc_conf_fd.write ( "ConnectTo=%s\n" % host2.name )
			tinc_conf_fd.close()
			bridge_name=con.interface.device.bridge_name(con.interface)
			create_fd=open(self.topology.get_deploy_script(host.name,"create"), "a")
			create_fd.write ( "ln -s $(pwd)/%s /etc/tincd/%s\n" % (tincname, tincname) )
			create_fd.close ()
			destroy_fd=open(self.topology.get_deploy_script(host.name,"destroy"), "a")
			destroy_fd.write ( "rm /etc/tincd/%s\n" % tincname )
			destroy_fd.close ()
			start_fd=open(self.topology.get_deploy_script(host.name,"start"), "a")
			start_fd.write ( "tincd --net=%s --chroot --pidfile=%s.pid\n" % (tincname, tincname) )
			start_fd.write ( "brctl addif %s %s\n" % (bridge_name, tincname ) )
			start_fd.write ( "ip link set %s up\n" %  tincname )
			start_fd.close ()
			stop_fd=open(self.topology.get_deploy_script(host.name,"stop"), "a")
			stop_fd.write ( "cat %s.pid | xargs kill\n" % tincname )
			stop_fd.close ()
		for con in self.connections:
			host = con.interface.device.host
			path = self.topology.get_deploy_dir(host.name) + "/" + tincname
			for con2 in self.connections:
				host2 = con2.interface.device.host
				path2 = self.topology.get_deploy_dir(host2.name) + "/" + tincname
				if not host.name == host2.name:
					shutil.copy(path+"/hosts/"+host.name, path2+"/hosts/"+host.name)
