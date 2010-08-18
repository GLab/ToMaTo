# -*- coding: utf-8 -*-

import generic, fault

class InternetConnector(generic.Connector):

	def init(self, topology, dom):
		self.topology = topology
		self.decode_xml(dom)
		self.save()		
		for connection in dom.getElementsByTagName ( "connection" ):
			con = generic.Connection()
			con.init (self, connection)
			con.bridge_special_name = con.interface.device.host.public_bridge
			self.connection_set.add ( con )

	def upcast(self):
		return self

	def encode_xml(self, dom, doc, internal):
		generic.Connector.encode_xml(self, dom, doc, internal)
		
	def decode_xml(self, dom):
		generic.Connector.decode_xml(self, dom)
		
	def write_aux_files(self):
		pass
	
	def write_control_script(self, host, script, fd):
		pass
		
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
				con = generic.Connection()
				con.init(self, x_con)
				self.connections_add(con)
		for con in self.connections_all():
			if not con.interface in cons:
				#deleted connection
				con.delete()		