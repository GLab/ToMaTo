# -*- coding: utf-8 -*-

from django.db import models

import generic

class EmulatedConnection(generic.Connection):
	delay = models.IntegerField(null=True)
	bandwidth = models.IntegerField(null=True)
	lossratio = models.FloatField(null=True)
	
	def __init__(self, connector, dom):
		self.connector = connector
		self.decode_xml(dom)
	
	def is_tinc(self):
		#TODO
		return True
	
	def encode_xml(self, dom, doc, internal):
		dom.setAttribute("delay", self.delay)
		dom.setAttribute("bandwidth", self.bandwidth)
		dom.setAttribute("lossratio", self.lossratio)
		if self.is_tinc():
			self.tinc.encode_xml(dom, doc, internal)
				
	def decode_xml(self, dom):
		generic.Connection.decode_xml(self, dom)
		self.delay = dom.getAttribute("delay")
		self.bandwidth = dom.getAttribute("bandwidth")
		self.lossratio = dom.getAttribute("lossratio")
		
	def write_control_script(self, host, script, fd):
		"""
		Write the control scrips for this object and its child objects
		"""
		if script == "start":
			pipe_id = int(self.bridge_id) * 10
			pipe_config=""
			fd.write("modprobe ipfw_mod\n")
			fd.write("ipfw add %d pipe %d via %s out\n" % ( pipe_id+1, pipe_id, self.bridge_name ) )
			if self.delay:
				pipe_config = pipe_config + " " + "delay %s" % self.delay
			if self.bandwidth:
				pipe_config = pipe_config + " " + "bw %s" % self.bandwidth
			fd.write("ipfw pipe %d config %s\n" % ( pipe_id, pipe_config ) )
			if self.lossratio:
				fd.write("ipfw add %d prob %s drop via %s out\n" % ( pipe_id, self.lossratio, self.bridge_name ) )
		if script == "stop":
			pipe_id = int(self.bridge_id) * 10
			fd.write("ipfw delete %d\n" % pipe_id )
			fd.write("ipfw delete %d\n" % ( pipe_id + 1 ) )