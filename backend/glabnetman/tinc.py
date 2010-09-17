# -*- coding: utf-8 -*-

from django.db import models

import dummynet, generic, config, hosts, os, subprocess, shutil, fault, util

class TincConnector(generic.Connector):
	
	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.save()
		for connection in dom.getElementsByTagName ( "connection" ):
			self.add_connection(connection)

	def add_connection(self, dom):
		con = TincConnection()
		con.init (self, dom)
		con.bridge_special_name = None
		self.connection_set.add ( con )
		self.save()
		return con
	
	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Connector.encode_xml(self, dom, doc, internal)
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)

	def tincname(self, con):
		return "tinc_%s" % con.id

	def start_run(self, task):
		generic.Connector.start_run(self, task)
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			host.free_port(con.upcast().tinc_port, task)		
			host.execute ( "tincd --net=%s" % tincname, task)
			if not config.remote_dry_run:
				assert host.interface_exists(tincname), "Tinc deamon did not start"
			host.execute ( "ifconfig %s 0.0.0.0 up" %  tincname, task)
			if self.type == "router":
				table_in = 1000 + 2 * con.id
				table_out = 1000 + 2 * con.id + 1 
				host.execute ( "ip addr add %s dev %s" % (con.upcast().gateway, con.bridge_name()), task )
				host.execute ( "ip link set up dev %s" % con.bridge_name(), task )
				host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_in, table_in, table_in ), task )
				host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_out, table_out, table_out ), task )
				host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( tincname, table_in ), task )
				host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( con.bridge_name(), table_out ), task )
				host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_in), table_in ), task )
				host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_out), table_out ), task )
				host.execute ( "ip route add table %s default dev %s" % ( table_in, con.bridge_name() ), task )
				host.execute ( "ip route add table %s default dev %s" % ( table_out, tincname ), task )
			else:
				host.bridge_connect(con.bridge_name(), tincname)
		self.state = generic.State.STARTED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def stop_run(self, task):
		generic.Connector.stop_run(self, task)
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			if self.type == "router":
				table_in = 1000 + 2 * con.id
				table_out = 1000 + 2 * con.id + 1 
				host.execute ( "iptables -t mangle -D PREROUTING -i %s -j MARK --set-mark %s" % ( tincname, table_in ), task )
				host.execute ( "iptables -t mangle -D PREROUTING -i %s -j MARK --set-mark %s" % ( con.bridge_name(), table_out ), task )
				host.execute ( "ip rule del fwmark %s table %s" % ( hex(table_in), table_in ), task )
				host.execute ( "ip rule del fwmark %s table %s" % ( hex(table_out), table_out ), task )
				host.execute ( "ip route del table %s default dev %s" % ( table_in, con.bridge_name() ), task )
				host.execute ( "ip route del table %s default dev %s" % ( table_out, tincname ), task )
			host.execute ( "tincd --net=%s -k" % tincname, task)
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def prepare_run(self, task):
		generic.Connector.prepare_run(self, task)
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			tincport = con.upcast().tinc_port 
			path = self.topology.get_control_dir(host.name) + "/" + tincname
			if not os.path.exists(path+"/hosts"):
				os.makedirs(path+"/hosts")
			subprocess.check_call (["openssl",  "genrsa",  "-out",  path + "/rsa_key.priv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			self_host_fd = open(path+"/hosts/"+tincname, "w")
			self_host_fd.write("Address=%s\n" % host.name)
			self_host_fd.write("Port=%s\n" % tincport )
			self_host_fd.write("Cipher=none\n" )
			self_host_fd.write("Digest=none\n" )
			if self.type == "router":
				self_host_fd.write("Subnet=%s\n" % util.calculate_subnet(con.upcast().gateway))
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
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			path = self.topology.get_control_dir(host.name) + "/" + tincname + "/"
			host.upload(path, self.topology.get_remote_control_dir() + "/" + tincname, task)
			host.execute ( "[ -e /etc/tinc/%s ] || ln -s %s/%s /etc/tinc/%s" % (tincname, self.topology.get_remote_control_dir(), tincname, tincname), task)
		self.state = generic.State.PREPARED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def destroy_run(self, task):
		generic.Connector.destroy_run(self, task)		
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			host.execute ( "rm /etc/tinc/%s" % tincname, task )
			host.execute ( "true", task )
		self.state = generic.State.CREATED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def change_possible(self, dom):
		pass
	
	def change_run(self, dom, task):
		oldcons = [con.interface for con in self.connections_all()]
		generic.Connector.change_run(self, dom, task)
		cons = [con.interface for con in self.connections_all()]
		if not oldcons == cons:
			oldstate = self.state
			if self.state == generic.State.STARTED:
				task.subtasks_total = task.subtasks_total + 1
				self.stop_run(task)
			if self.state == generic.State.PREPARED:
				task.subtasks_total = task.subtasks_total + 1
				self.destroy_run(task)
			if oldstate == generic.State.STARTED or oldstate == generic.State.PREPARED:
				task.subtasks_total = task.subtasks_total + 1
				self.prepare_run(task)
			if oldstate == generic.State.STARTED:
				task.subtasks_total = task.subtasks_total + 1
				self.start_run(task)
		self.save()

class TincConnection(dummynet.EmulatedConnection):
	tinc_port = models.IntegerField(null=True)
	gateway = models.CharField(max_length=18, null=True) 
	
	def init(self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
		self.bridge_id = self.interface.device.host.next_free_bridge()		
		self.bridge_special_name = ""
		self.save()
	
	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		dummynet.EmulatedConnection.encode_xml(self, dom, doc, internal)
		if self.gateway:
			dom.setAttribute("gateway", self.gateway)
		if internal:
			if self.tinc_port:
				dom.setAttribute("tinc_port", str(self.tinc_port))
		
	def decode_xml(self, dom):
		dummynet.EmulatedConnection.decode_xml(self, dom)
		self.gateway = util.get_attr(dom, "gateway", default="10.1.1.254/24")
		if not len(self.gateway.split("/")) == 2:
			self.gateway = self.gateway + "/24"
		
	def start_run(self, task):
		dummynet.EmulatedConnection.start_run(self, task)

	def stop_run(self, task):
		dummynet.EmulatedConnection.stop_run(self, task)

	def prepare_run(self, task):
		if not self.tinc_port:
			self.tinc_port = self.interface.device.host.next_free_port()
			self.save()
		dummynet.EmulatedConnection.prepare_run(self, task)

	def destroy_run(self, task):
		self.tinc_port=None
		self.save()
		dummynet.EmulatedConnection.destroy_run(self, task)				

	def change_run(self, dom, task):
		self.decode_xml(dom)
		dummynet.EmulatedConnection.change_run(self, dom, task)