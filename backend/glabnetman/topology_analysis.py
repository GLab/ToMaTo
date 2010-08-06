# -*- coding: utf-8 -*-

import re

class Result():
	def __init__(self):
		self.problems=[]
		self.warnings=[]
		self.hints=[]
	

def analyze(top):
	res = Result()
	if len(top.devices) == 0:
		res.problems.append("No devices specified")
	_check_fully_connected(top, res)
	_check_interface_connection_count(top, res)
	_check_connectors_connection_count(top, res)
	_check_real_connectors(top, res)
	_check_connectors_ip_structure(top, res)
	_check_connection_performance(top, res)
	return res

def _check_fully_connected(top, res):
	reachable=set()
	todo=set()
	unreachable=set()
	#put everything in unreachable
	for device in top.devices.values():
		unreachable.add(device)
	#select a strating device and put it in todo
	start=iter(unreachable).next()
	todo.add(start)
	while len(todo)>0:
		cur=iter(todo).next()
		#mark cur as reachable and done
		reachable.add(cur)
		unreachable.remove(cur)
		todo.remove(cur)
		for interface in cur.interfaces.values():
			if interface.connection:
				for connection in interface.connection.connector.connections:
					dev=connection.interface.device
					if not dev in reachable:
						todo.add(dev)
	if len(unreachable):
		res.warnings.append("Topology is not fully connected, e.g. %s and %s" % (iter(reachable).next().id, iter(unreachable).next().id ) )
	
def _check_interface_connection_count(top,res):
	con={}
	for device in top.devices.values():
		for interface in device.interfaces.values():
			con[repr(interface)]=[]
	for connector in top.connectors.values():
		for connection in connector.connections:
			con[repr(connection.interface)].append(connector)
	for interface, connectors in con.iteritems():
		if len(connectors)==0:
			res.warnings.append("Interface %s is not connected" % interface)
		if len(connectors)>1:
			res.problems.append("Interface %s is connected multiple times" % interface)
				
def _check_connectors_connection_count(top,res):
	for connector in top.connectors.values():
		if len(connector.connections)==0:
			res.problems.append("Connector %s is not connected" % connector.id)
		if len(connector.connections)==1 and not connector.type == "real":
			res.warnings.append("Connector %s is only connected once" % connector.id)
			
def _check_real_connectors(top,res):
	real=[]
	for connector in top.connectors.values():
		if connector.type == "real":
			real.append(connector)
	if len(real)==0:
		res.warning.append("No real network connector used")
	if len(real)>1:
		res.hints.append("Multiple real world connectors can be joined")

def _check_connectors_ip_structure(top,res):
	for connector in top.connectors.values():
		dhcp_server=set()
		ip_addresses=set()
		dhcp_clients=set()
		for connection in connector.connections:
			if connection.interface.attributes.has_key("ip4_address"):
				ip=connection.interface.attributes["ip4_address"]
				if ip in ip_addresses:
					res.warnings.append("Duplicate IP address %s on %s" % ( ip, connector.id ) )
				ip_addresses.add(ip)
			if connection.interface.attributes.has_key("use_dhcp"):
				dhcp_clients.add(connection.interface.device.id)
			if connection.interface.device.type == "dhcpd":
				dhcp_server.add(connection.interface.device.id)
		if len(dhcp_server)>1:
			res.warnings.append("Multiple dhcp servers on connector %s: %s" % ( connector.id, dhcp_server ) )
		if len(dhcp_clients)>0 and len(dhcp_server)==0 and not connector.type=="real":
			res.hints.append("No dhcp server configured on %s but clients configured to use dhcpd: %s" % ( connector.id, dhcp_clients ) )
		if len(dhcp_clients)==0 and len(dhcp_server)>0:
			res.hints.append("Dhcp server configured on %s but no clients using it: %s" % ( connector.id, dhcp_servers ) )
				
def _check_connection_performance(top,res):
	for connector in top.connectors.values():
		for connection in connector.connections:
			if connection.lossratio:
				r=float(connection.lossratio)
				if (r<0.0) or (r>1.0):
					res.problems.append("Loss ratio for %s must be in [0..1]" % repr(connection))
				if r==1:
					res.warning.append("Loss ratio for %s set to 1, that means no connection" % repr(connection))
			if connection.delay:
				d=connection.delay
				if not re.match("\d+ms",d):
					res.problems.append("Delay for %s must be in the form [0-9]+ms" % repr(connection))