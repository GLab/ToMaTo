# -*- coding: utf-8 -*-

from django.db import models

import dummynet, generic, hosts, os, subprocess, shutil, fault, util

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
		generic.Connector.encode_xml(self, dom, doc, internal)
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)

	def tincname(self, con):
		return "tinc_%s" % con.id

	def tincport(self, con):
		return con.emulatedconnection.tincconnection.tinc_port

	def start_run(self, task):
		generic.Connector.start_run(self, task)
		for con in self.connections_all():
			host = con.interface.device.host
			tincname = self.tincname(con)
			host.execute ( "tincd --net=%s" % tincname, task)
			host.execute ( "ifconfig %s 0.0.0.0 up" %  tincname, task)
			if self.type == "router":
				table_in = 1000 + 2 * con.id
				table_out = 1000 + 2 * con.id + 1 
				host.execute ( "ifconfig %s %s netmask %s up" % (con.bridge_name(), con.upcast().gateway_ip, con.upcast().gateway_netmask), task )
				host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_in, table_in, table_in ), task )
				host.execute ( "grep '^%s ' /etc/iproute2/rt_tables || echo \"%s %s\" >> /etc/iproute2/rt_tables" % ( table_out, table_out, table_out ), task )
				host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( tincname, table_in ), task )
				host.execute ( "iptables -t mangle -A PREROUTING -i %s -j MARK --set-mark %s" % ( con.bridge_name(), table_out ), task )
				host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_in), table_in ), task )
				host.execute ( "ip rule add fwmark %s table %s" % ( hex(table_out), table_out ), task )
				host.execute ( "ip route add table %s default dev %s" % ( table_in, con.bridge_name() ), task )
				host.execute ( "ip route add table %s default dev %s" % ( table_out, tincname ), task )
			else:
				host.execute ( "brctl addif %s %s" % (con.bridge_name(), tincname ), task)
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
			#FIXME: write Subnet entry
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
			path = self.topology.get_control_dir(host.name) + "/" + tincname
			host.upload(path, self.topology.get_remote_control_dir() + "/" + tincname, task)
			tincname = self.tincname(con)
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
		cons=set()
		for x_con in dom.getElementsByTagName("connection"):
			try:
				device_name = x_con.getAttribute("device")
				device = self.topology.devices_get(device_name)
				iface_name = x_con.getAttribute("interface")
				iface = device.interfaces_get(iface_name)
				cons.add(iface)
			except generic.Device.DoesNotExist:
				raise fault.new(fault.UNKNOWN_INTERFACE, "Unknown connection device %s" % device_name)
			except generic.Interface.DoesNotExist:
				raise fault.new(fault.UNKNOWN_INTERFACE, "Unknown connection interface %s.%s" % (device_name, iface_name))
			try:
				con = self.connections_get(iface)				
			except generic.Connection.DoesNotExist:
				#new connection
				con = TincConnection()
				con.init(self, x_con)
				self.connections_add(con)
		for con in self.connections_all():
			if not con.interface in cons:
				#deleted connection
				con.delete()			

class TincConnection(dummynet.EmulatedConnection):
	tinc_port = models.IntegerField()
	gateway_ip = models.CharField(max_length=15, null=True) 
	gateway_netmask = models.CharField(max_length=15, null=True)
	
	def init(self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
		self.bridge_id = self.interface.device.host.next_free_bridge()		
		self.tinc_port = self.interface.device.host.next_free_port()
		self.save()
	
	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		dummynet.EmulatedConnection.encode_xml(self, dom, doc, internal)
		if self.gateway_ip:
			dom.setAttribute("gateway_ip", self.gateway_ip)
		if self.gateway_netmask:
			dom.setAttribute("gateway_netmask", self.gateway_netmask)
		if internal:
			dom.setAttribute("tinc_port", self.tinc_port)
		
	def decode_xml(self, dom):
		dummynet.EmulatedConnection.decode_xml(self, dom)
		self.gateway_ip = util.get_attr(dom, "gateway_ip", default=None)
		self.gateway_netmask = util.get_attr(dom, "gateway_netmask", default=None)
		
	def start_run(self, task):
		dummynet.EmulatedConnection.start_run(self, task)

	def stop_run(self, task):
		dummynet.EmulatedConnection.stop_run(self, task)

	def prepare_run(self, task):
		dummynet.EmulatedConnection.prepare_run(self, task)

	def destroy_run(self, task):
		dummynet.EmulatedConnection.destroy_run(self, task)				
