# -*- coding: utf-8 -*-

from connector import *
from util import *
import resource
import os, subprocess, shutil

class TincConnector(Connector):
	"""
	This class represents a tinc connector
	"""

	tinc_ids = resource.Store(1,10000)

	def __init__(self, topology, dom, load_ids):
		"""
		Creates a tinc connector object
		@param topology the parent topology object
		@param dom the xml dom object of the connector
		@param load_ids whether to lod or ignore assigned ids
		"""
		Connector.__init__(self, topology, dom, load_ids)
		self.decode_xml(dom, load_ids)
		Connection.port_number = property(curry(Connection.get_attr, "port_number"), curry(Connection.set_attr, "port_number"))
		Connection.tinc_id = property(curry(Connection.get_attr, "tinc_id"), curry(Connection.set_attr, "tinc_id"))

	def retake_resources(self):
		"""
		Take all resources that this object and child objects once had. Fields containing the ids of assigned resources control which resources will be taken.
		"""
		for con in self.connections:
			con.retake_resources()
			if con.port_number:
				con.interface.device.host.ports.take_specific(con.port_number)
			if con.tinc_id:
				TincConnector.tinc_ids.take_specific(con.tinc_id)

	def take_resources(self):
		"""
		Take free resources for all unassigned resource slots of thos object and its child objects. The number of the resources will be stored in internal fields.
		"""
		for con in self.connections:
			con.take_resources()
			if not con.port_number:
				con.port_number = str(con.interface.device.host.ports.take())
			if not con.tinc_id:
				con.tinc_id = TincConnector.tinc_ids.take()

	def free_resources(self):
		"""
		Free all resources for all resource slots of this object and its child objects.
		"""
		for con in self.connections:
			con.free_resources()
			con.interface.device.host.ports.free(con.port_number)
			con.port_number = None
			TincConnector.tinc_ids.free(con.tinc_id)
			con.tinc_id = None

	def decode_xml ( self, dom, load_ids ):
		"""
		Read the attributes from the xml dom object
		@param dom the xml dom object to read the data from
		@load_ids whether to load or ignore assigned ids
		"""
		if not load_ids:
			for con in self.connections:
				con.port_number = None
				con.tinc_id = None

	def encode_xml ( self, dom, doc, print_ids ):
		"""
		Encode the object to an xml dom object
		@param dom the xml dom object to write the data to
		@param doc the xml document needed to create child elements
		@print_ids whether to include or ignore assigned ids
		"""
		Connector.encode_xml(self,dom,doc,print_ids)
		if not print_ids:
			for con in dom.getElementsByTagName ( "connection" ):
				if con.hasAttribute("port_number"):
					con.removeAttribute("port_number")
				if con.hasAttribute("tinc_id"):
					con.removeAttribute("tinc_id")

	def tincname(self, con):
		return "tinc_" + con.tinc_id
				

	def write_aux_files(self):
		for con in self.connections:
			host = con.interface.device.host
			tincname = self.tincname(con)
			path = self.topology.get_control_dir(host.name) + "/" + tincname
			if not os.path.exists(path+"/hosts"):
				os.makedirs(path+"/hosts")
			subprocess.check_call (["openssl",  "genrsa",  "-out",  path + "/rsa_key.priv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			self_host_fd = open(path+"/hosts/"+tincname, "w")
			self_host_fd.write("Address=%s\n" % host.name)
			self_host_fd.write("Port=%s\n" % con.port_number )
			self_host_fd.write("Cipher=none\n" )
			self_host_fd.write("Digest=none\n" )
			subprocess.check_call (["openssl",  "rsa", "-pubout", "-in",  path + "/rsa_key.priv", "-out",  path + "/hosts/" + tincname + ".pub"], stderr=subprocess.PIPE)
			self_host_pub_fd = open(path+"/hosts/"+tincname+".pub", "r")
			shutil.copyfileobj(self_host_pub_fd, self_host_fd)
			self_host_fd.close()
			self_host_pub_fd.close()
			tinc_conf_fd = open(path+"/tinc.conf", "w")
			tinc_conf_fd.write ( "Mode=%s\n" % self.type )
			tinc_conf_fd.write ( "Name=%s\n" % tincname )
			tinc_conf_fd.write ( "AddressFamily=ipv4\n" )
			for con2 in self.connections:
				host2 = con2.interface.device.host
				tincname2 = self.tincname(con2)
				if not tincname == tincname2:
					tinc_conf_fd.write ( "ConnectTo=%s\n" % tincname2 )
			tinc_conf_fd.close()
		for con in self.connections:
			host = con.interface.device.host
			tincname = self.tincname(con)
			path = self.topology.get_control_dir(host.name) + "/" + tincname
			for con2 in self.connections:
				host2 = con2.interface.device.host
				tincname2 = self.tincname(con2)
				path2 = self.topology.get_control_dir(host2.name) + "/" + tincname2
				if not tincname == tincname2:
					shutil.copy(path+"/hosts/"+tincname, path2+"/hosts/"+tincname)

	def write_control_script(self, host, script, fd):
		"""
		Write the control scrips for this object and its child objects
		"""
		for con in self.connections:
			if con.interface.device.host_name == host.name:
				con.write_control_script(host, script, fd)
		for con in self.connections:
			tincname = self.tincname(con)
			if script == "prepare":
				fd.write ( "[ -e /etc/tinc/%s ] || ln -s %s/%s /etc/tinc/%s\n" % (tincname, self.topology.get_remote_control_dir(), tincname, tincname) )
			if script == "destroy":
				fd.write ( "rm /etc/tinc/%s\n" % tincname )
				fd.write ( "true\n" )
			if script == "start":
				fd.write ( "tincd --net=%s\n" % tincname )
				#FIXME: brctl does not work for routing
				fd.write ( "brctl addif %s %s\n" % (con.bridge_name, tincname ) )
				fd.write ( "ip link set %s up\n" %  tincname )
			if script == "stop":
				fd.write ( "cat /var/run/tinc.%s.pid | xargs kill\n" % tincname )
				fd.write ( "rm /var/run/tinc.%s.pid\n" % tincname )
				fd.write ( "true\n" )

	def __str__(self):
		return "tinc %s %s" % ( self.type, self.id )