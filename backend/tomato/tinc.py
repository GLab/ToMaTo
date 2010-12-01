# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.db import models

import dummynet, generic, config, hosts, os, subprocess, shutil, fault, util

class TincConnector(generic.Connector):
	
	def add_connection(self, dom):
		con = TincConnection()
		con.init (self, dom)
		self.connection_set.add ( con )
		self.save()
		return con
	
	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Connector.encode_xml(self, dom, doc, internal)
		
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
			if host:
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
			if host:
				host.execute ( "rm /etc/tinc/%s" % tincname, task )
				host.execute ( "true", task )
		self.state = generic.State.CREATED
		self.save()
		task.subtasks_done = task.subtasks_done + 1

	def configure(self, properties, task):
		generic.Connector.configure(self, properties, task)
	
	def connections_add(self, iface_name, properties, task):
		iface = self.topology.interfaces_get(iface_name)
		if self.state == generic.State.STARTED or self.state == generic.State.PREPARED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to started or prepared connector: %s -> %s" % (iface_name, self.name) )
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to running device: %s -> %s" % (iface_name, self.name) )
		if iface.is_connected():
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot add connections to connected interface: %s -> %s" % (iface_name, self.name) )
		con = TincConnection ()
		con.connector = self
		con.interface = iface
		con.configure(properties, task)
		con.save()

	def connections_configure(self, iface_name, properties, task):
		iface = self.topology.interfaces_get(iface_name)
		con = self.connections_get(iface)
		con.configure(properties, task)
		con.save()	
	
	def connections_delete(self, iface_name, task):
		iface = self.topology.interfaces_get(iface_name)
		if self.state == generic.State.STARTED or self.state == generic.State.PREPARED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to started or prepared connector: %s -> %s" % (iface_name, self.name) )
		if iface.device.state == generic.State.STARTED:
			raise fault.Fault(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot delete connections to running devices: %s -> %s" % (iface_name, self.name) )
		con = self.connections_get(iface)
		con.delete()

	def get_resource_usage(self):
		if self.state == generic.State.CREATED:
			disk = 0
		else:
			disk = 10000   
		if self.state == generic.State.STARTED:
			ports = len(self.connections_all())
			memory = ( 1200 + 250 * ports ) * 1024
		else:
			memory = 0
			ports = 0
		traffic = 0
		for con in self.connections_all():
			dev = con.interface.device
			if dev.host:
				br = self.bridge_name(con.interface)
				traffic += int(dev.host.get_result("[ -f /sys/class/net/%s/statistics/rx_bytes ] && cat /sys/class/net/%s/statistics/rx_bytes || echo 0" % (br, br) ))
				traffic += int(dev.host.get_result("[ -f /sys/class/net/%s/statistics/tx_bytes ] && cat /sys/class/net/%s/statistics/tx_bytes || echo 0" % (br, br) ))
		return {"disk": disk, "memory": memory, "ports": ports, "traffic": traffic}		


class TincConnection(dummynet.EmulatedConnection):
	tinc_port = models.IntegerField(null=True)
	gateway = models.CharField(max_length=18, null=True) 
	
	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		dummynet.EmulatedConnection.encode_xml(self, dom, doc, internal)
		if self.gateway and self.connector.type == "router":
			dom.setAttribute("gateway", self.gateway)
		if internal:
			if self.tinc_port:
				dom.setAttribute("tinc_port", str(self.tinc_port))
		
	def configure(self, properties, task):
		dummynet.EmulatedConnection.configure(self, properties, task)
		if "gateway" in properties:
			assert self.connector.state == generic.State.CREATED, "Cannot change gateways on prepared or started router: %s" % self
			self.gateway = properties["gateway"]
		if self.connector.type == "router":
			if not self.gateway:
				self.gateway = "10.1.1.254/24" 
			if not len(self.gateway.split("/")) == 2:
				self.gateway = self.gateway + "/24"
		
	def start_run(self, task):
		dummynet.EmulatedConnection.start_run(self, task)

	def stop_run(self, task):
		dummynet.EmulatedConnection.stop_run(self, task)

	def prepare_run(self, task):
		if not self.bridge_id:
			self.bridge_id = self.interface.device.host.next_free_bridge()		
			self.save()
		if not self.tinc_port:
			self.tinc_port = self.interface.device.host.next_free_port()
			self.save()
		dummynet.EmulatedConnection.prepare_run(self, task)

	def destroy_run(self, task):
		self.bridge_id=None
		self.tinc_port=None
		self.save()
		dummynet.EmulatedConnection.destroy_run(self, task)
