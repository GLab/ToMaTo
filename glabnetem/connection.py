# -*- coding: utf-8 -*-

from util import *

class Connection(XmlObject):
  
	def __init__ ( self, connector, dom, load_ids ):
		self.connector = connector
		self.decode_xml ( dom, load_ids )
		self.device = connector.topology.devices[self.device_id]
		self.interface = self.device.interfaces[self.interface_id]
		self.interface.connection = self

	def encode_xml (self, dom, doc, print_ids):
		XmlObject.encode_xml(self, dom)
		if not print_ids:
			if dom.hasAttribute("bridge_id"):
				dom.removeAttribute("bridge_id")
				if dom.hasAttribute("bridge_name"):
					dom.removeAttribute("bridge_name")

	def decode_xml (self, dom, load_ids):
		if not load_ids:
			if dom.hasAttribute("bridge_id"):
				dom.removeAttribute("bridge_id")
				if dom.hasAttribute("bridge_name"):
					dom.removeAttribute("bridge_name")
		XmlObject.decode_xml(self,dom)

	bridge_name=property(curry(XmlObject.get_attr, "bridge"), curry(XmlObject.set_attr, "bridge"))
	bridge_id=property(curry(XmlObject.get_attr, "bridge_id"), curry(XmlObject.set_attr, "bridge_id"))
	device_id=property(curry(XmlObject.get_attr, "device"), curry(XmlObject.set_attr, "device"))
	interface_id=property(curry(XmlObject.get_attr, "interface"), curry(XmlObject.set_attr, "interface"))
	
	delay=property(curry(XmlObject.get_attr, "delay"), curry(XmlObject.set_attr, "delay"))
	bandwidth=property(curry(XmlObject.get_attr, "bandwidth"), curry(XmlObject.set_attr, "bandwidth"))
	lossratio=property(curry(XmlObject.get_attr, "lossratio"), curry(XmlObject.set_attr, "lossratio"))
	
	def write_deploy_script(self):
		host = self.device.host
		start_fd=open(self.connector.topology.get_deploy_script(host.name,"start"), "a")
		start_fd.write("brctl addbr %s\n" % self.bridge_name )
		start_fd.write("ip link set %s up\n" % self.bridge_name )
		if self.bridge_id:
			pipe_id = int(self.bridge_id) * 10
			pipe_config=""
			start_fd.write("modprobe ipfw_mod\n")
			start_fd.write("ipfw add %d pipe %d via %s out\n" % ( pipe_id+1, pipe_id, self.bridge_name ) )
			if self.delay:
				pipe_config = pipe_config + " " + "delay %s" % self.delay
			if self.bandwidth:
				pipe_config = pipe_config + " " + "bw %s" % self.bandwidth
			if pipe_config:
				start_fd.write("ipfw pipe %d config %s\n" % ( pipe_id, pipe_config ) )
			if self.lossratio:
				start_fd.write("ipfw add %d prob %s drop via %s out\n" % ( pipe_id, self.lossratio, self.bridge_name ) )
		start_fd.close()
		stop_fd=open(self.connector.topology.get_deploy_script(host.name,"stop"), "a")
		stop_fd.write("ip link set %s down\n" % self.bridge_name )
		stop_fd.write("brctl delbr %s\n" % self.bridge_name )
		if self.bridge_id:
			pipe_id = int(self.bridge_id) * 10
			stop_fd.write("ipfw delete %d\n" % pipe_id )
			stop_fd.write("ipfw delete %d\n" % ( pipe_id + 1 ) )
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
