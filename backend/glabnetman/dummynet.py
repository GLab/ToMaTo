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
	
	def upcast(self):
		if self.is_tinc():
			return self.tincconnection
		return self

	def is_tinc(self):
		try:
			self.tincconnection
			return True
		except:
			return False
	
	def encode_xml(self, dom, doc, internal):
		generic.Connection.encode_xml(self, dom, doc, internal)
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

	def start(self, task):
		generic.Connection.start(self, task)
		host = self.interface.device.host
		pipe_id = int(self.bridge_id) * 10
		pipe_config=""
		host.execute("modprobe ipfw_mod", task)
		host.execute("ipfw add %d pipe %d via %s out" % ( pipe_id+1, pipe_id, self.bridge_name() ), task)
		if self.delay:
			pipe_config = pipe_config + " " + "delay %sms" % self.delay
		if self.bandwidth:
			pipe_config = pipe_config + " " + "bw %sk" % self.bandwidth
		host.execute("ipfw pipe %d config %s" % ( pipe_id, pipe_config ), task)
		if self.lossratio:
			host.execute("ipfw add %d prob %s drop via %s out" % ( pipe_id, self.lossratio, self.bridge_name() ), task)

	def stop(self, task):
		generic.Connection.stop(self, task)
		host = self.interface.device.host
		pipe_id = int(self.bridge_id) * 10
		host.execute("ipfw delete %d" % pipe_id, task)
		host.execute("ipfw delete %d" % ( pipe_id + 1 ), task)
			
	def prepare(self, task):
		generic.Connection.prepare(self, task)

	def destroy(self, task):
		generic.Connection.destroy(self, task)
