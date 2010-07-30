# -*- coding: utf-8 -*-

from topology import *

class TopologyAnalysis():
	def __init__(self, top):
		self.problems=[]
		self.warnings=[]
		self.hints=[]
		self.analyze(top)
		
	def analyze(self, top):
		if len(top.devices) == 0:
			self.problems.append("No devices specified")
		self.check_fully_connected(top)
		self.check_interface_connection_count(top)
		self.check_connectors_connection_count(top)
		self.check_real_connectors(top)

	def check_fully_connected(self, top):
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
			self.warnings.append("Topology is not fully connected, e.g. %s and %s" % (iter(reachable).next().id, iter(unreachable).next().id ) )
		
	def check_interface_connection_count(self, top):
		con={}
		for device in top.devices.values():
			for interface in device.interfaces.values():
				con[repr(interface)]=[]
		for connector in top.connectors.values():
			for connection in connector.connections:
				con[repr(connection.interface)].append(connector)
		for interface, connectors in con.iteritems():
			if len(connectors)==0:
				self.warnings.append("Interface %s is not connected" % interface)
			if len(connectors)>1:
				self.problems.append("Interface %s is connected multiple times" % interface)
				
	def check_connectors_connection_count(self, top):
		for connector in top.connectors.values():
			if len(connector.connections)==0:
				self.problems.append("Connector %s is not connected" % connector.id)
			if len(connector.connections)==1 and not connector.type == "real":
				self.warnings.append("Connector %s is only connected once" % connector.id)
				
	def check_real_connectors(self, top):
		real=[]
		for connector in top.connectors.values():
			if connector.type == "real":
				real.append(connector)
		if len(real)==0:
			self.warning.append("No real network connector used")
		if len(real)>1:
			self.hints.append("Multiple real world connectors can be joined")

