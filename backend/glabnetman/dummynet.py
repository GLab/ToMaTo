# -*- coding: utf-8 -*-

from django.db import models

import re
import generic, hosts, util

class EmulatedConnection(generic.Connection):
	delay = models.IntegerField(null=True)
	bandwidth = models.IntegerField(null=True)
	lossratio = models.FloatField(null=True)
	
	def init(self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
		self.bridge_id = self.interface.device.host.next_free_bridge()		
		self.save()
	
	def is_tinc(self):
		try:
			self.tincconnection
			return True
		except:
			return False
	
	def encode_xml(self, dom, doc, internal):
		if self.delay:
			dom.setAttribute("delay", "%sms" % self.delay)
		if self.bandwidth:
			dom.setAttribute("bandwidth", "%sk" % self.bandwidth)
		if self.lossratio:
			dom.setAttribute("lossratio", str(self.lossratio))
		if self.is_tinc():
			self.tincconnection.encode_xml(dom, doc, internal)
				
	def decode_xml(self, dom):
		generic.Connection.decode_xml(self, dom)
		self.delay = re.match("(\d+)ms", util.get_attr(dom, "delay", default="0ms")).group(1)
		self.bandwidth = re.match("(\d+)k", util.get_attr(dom, "bandwidth", default="0k")).group(1)
		self.lossratio = util.get_attr(dom,"lossratio", default=0.0)

	def write_aux_files(self):
		generic.Connection.write_aux_files(self)
	
	def write_control_script(self, host, script, fd):
		"""
		Write the control scrips for this object and its child objects
		"""
		generic.Connection.write_control_script(self, host, script, fd)
		if script == "start":
			pipe_id = int(self.bridge_id) * 10
			pipe_config=""
			fd.write("modprobe ipfw_mod\n")
			fd.write("ipfw add %d pipe %d via %s out\n" % ( pipe_id+1, pipe_id, self.bridge_name() ) )
			if self.delay:
				pipe_config = pipe_config + " " + "delay %sms" % self.delay
			if self.bandwidth:
				pipe_config = pipe_config + " " + "bw %sk" % self.bandwidth
			fd.write("ipfw pipe %d config %s\n" % ( pipe_id, pipe_config ) )
			if self.lossratio:
				fd.write("ipfw add %d prob %s drop via %s out\n" % ( pipe_id, self.lossratio, self.bridge_name() ) )
		if script == "stop":
			pipe_id = int(self.bridge_id) * 10
			fd.write("ipfw delete %d\n" % pipe_id )
			fd.write("ipfw delete %d\n" % ( pipe_id + 1 ) )