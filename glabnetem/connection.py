# -*- coding: utf-8 -*-

from util import *

class Connection(XmlObject):
  
	def __init__ ( self, connector, dom ):
		self.connector = connector
		XmlObject.decode_xml(self,dom)
		self.device = connector.topology.devices[self.device_id]
		self.interface = self.device.interfaces[self.interface_id]
		self.interface.connection = self

	def encode_xml (self, dom, doc):
		XmlObject.encode_xml(self, dom)

	bridge_name=property(curry(XmlObject.get_attr, "bridge"), curry(XmlObject.set_attr, "bridge"))
	bridge_id=property(curry(XmlObject.get_attr, "bridge_id"), curry(XmlObject.set_attr, "bridge_id"))
	device_id=property(curry(XmlObject.get_attr, "device"), curry(XmlObject.set_attr, "device"))
	interface_id=property(curry(XmlObject.get_attr, "interface"), curry(XmlObject.set_attr, "interface"))
	
	delay=property(curry(XmlObject.get_attr, "delay"), curry(XmlObject.set_attr, "delay"))
	bandwidth=property(curry(XmlObject.get_attr, "bandwidth"), curry(XmlObject.set_attr, "bandwidth"))
	lossrate=property(curry(XmlObject.get_attr, "lossrate"), curry(XmlObject.set_attr, "lossrate"))
	
	def write_deploy_script(self):
		start_fd=open(self.connector.topology.get_deploy_script(host.name,"start"), "a")
		start_fd.write("brctl addbr %s\n" % self.bridge_name )
		start_fd.write("ip link set %s up\n" % self.bridge_name )
		if self.bridge_id:
			pipe_id = self.bridge_id * 10
			pipe_config=""
			start_fd.write("ipfw add %s pipe %s via %s out\n" % ( pipe_id, pipe_id, self.bridge_name ) )
			if self.delay:
				pipe_config = pipe_config + " " + "delay %s" % self.delay
			if self.bandwidth:
				pipe_config = pipe_config + " " + "bw %s" % self.bandwidth
			if pipe_config:
				start_fd.write("ipfw pipe %s config %s\n" % ( pipe_id, pipe_config ) )
			if self.lossrate:
				start_fd.write("ipfw add %s prob %s via %s out drop\n" % ( pipe_id+1, self.lossrate, self.bridge_name ) )
				
		start_fd.close()
		stop_fd=open(self.topology.get_deploy_script(host.name,"stop"), "a")
		stop_fd.write("ip link set %s down\n" % self.bridge_name )
		stop_fd.write("brctl delbr %s\n" % self.bridge_name )
		if self.bridge_id:
			pipe_id = self.bridge_id * 10
			stop_fd.write("ipfw remove %s\n" % pipe_id )
		stop_fd.close()
		
	
	def retake_resources(self):
		if self.bridge_id:
			self.device.host.bridge_ids.take_specific(self.bridge_id)
			self.bridge_name = "gbr" + self.bridge_id

	def take_resources(self):
		if not self.bridge_id and not self.bridge_name:
			self.bridge_id = self.device.host.bridge_ids.take()
			self.bridge_name = "gbr" + self.bridge_id

	def free_resources(self):
		if self.bridge_id:
			self.device.host.bridge_ids.free(self.bridge_id)
			self.bridge_id = None
			self.bridge_name = None
