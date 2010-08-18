# -*- coding: utf-8 -*-

from django.db import models

import dummynet, generic, hosts, os, subprocess, shutil

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
	
	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		pass
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)

	def tincname(self, con):
		return "tinc_%s" % con.emulatedconnection.tincconnection.tinc_id

	def tincport(self, con):
		return con.emulatedconnection.tincconnection.tinc_port

	def write_aux_files(self):
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			tincport = self.tincport(con) 
			path = self.topology.get_control_dir(host.name) + "/" + tincname
			if not os.path.exists(path+"/hosts"):
				os.makedirs(path+"/hosts")
			subprocess.check_call (["openssl",  "genrsa",  "-out",  path + "/rsa_key.priv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			self_host_fd = open(path+"/hosts/"+tincname, "w")
			self_host_fd.write("Address=%s\n" % host.name)
			self_host_fd.write("Port=%s\n" % tincport )
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
			for con2 in self.connections_all():
				host2 = con2.interface.device.host
				tincname2 = self.tincname(con2)
				if not tincname == tincname2:
					tinc_conf_fd.write ( "ConnectTo=%s\n" % tincname2 )
			tinc_conf_fd.close()
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			path = self.topology.get_control_dir(host.name) + "/" + tincname
			for con2 in self.connections_all():
				host2 = con2.interface.device.host
				tincname2 = self.tincname(con2)
				path2 = self.topology.get_control_dir(host2.name) + "/" + tincname2
				if not tincname == tincname2:
					shutil.copy(path+"/hosts/"+tincname, path2+"/hosts/"+tincname)

	def write_control_script(self, host, script, fd):
		"""
		Write the control scrips for this object and its child objects
		"""
		for con in self.connections_all():
			if con.interface.device.host.name == host.name:
				con.emulatedconnection.tincconnection.write_control_script(host, script, fd)
		for con in self.connections_all():
			tincname = self.tincname(con)
			if script == "prepare":
				fd.write ( "[ -e /etc/tinc/%s ] || ln -s %s/%s /etc/tinc/%s\n" % (tincname, self.topology.get_remote_control_dir(), tincname, tincname) )
			if script == "destroy":
				fd.write ( "rm /etc/tinc/%s\n" % tincname )
				fd.write ( "true\n" )
			if script == "start":
				fd.write ( "tincd --net=%s\n" % tincname )
				#FIXME: brctl does not work for routing
				fd.write ( "brctl addif %s %s\n" % (con.bridge_name(), tincname ) )
				fd.write ( "ip link set %s up\n" %  tincname )
			if script == "stop":
				fd.write ( "cat /var/run/tinc.%s.pid | xargs kill\n" % tincname )
				fd.write ( "rm /var/run/tinc.%s.pid\n" % tincname )
				fd.write ( "true\n" )


class TincConnection(dummynet.EmulatedConnection):
	tinc_id = models.IntegerField()
	tinc_port = models.IntegerField()
	
	def init(self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
		self.bridge_id = self.interface.device.host.next_free_bridge()		
		self.tinc_id = next_free_id(self.interface.device.host)
		self.tinc_port = self.interface.device.host.next_free_port()
		self.save()
	
	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		dummynet.EmulatedConnection.encode_xml(self, dom, doc, internal)
		if internal:
			dom.setAttribute("tinc_id", self.tinc_id)
			dom.setAttribute("tinc_port", self.tinc_port)
		
	def decode_xml(self, dom):
		dummynet.EmulatedConnection.decode_xml(self, dom)
		
	def write_aux_files(self):
		dummynet.EmulatedConnection.write_aux_files(self)
	
	def write_control_script(self, host, script, fd):
		dummynet.EmulatedConnection.write_control_script(self, host, script, fd)
		