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
			dom.setAttribute("delay", str(self.delay))
		if self.bandwidth:
			dom.setAttribute("bandwidth", str(self.bandwidth))
		if self.lossratio:
			dom.setAttribute("lossratio", str(self.lossratio))
				
	def decode_xml(self, dom):
		generic.Connection.decode_xml(self, dom)
		self.delay = util.get_attr(dom, "delay", default="0")
		self.bandwidth = util.get_attr(dom, "bandwidth", default="0")
		self.lossratio = util.get_attr(dom,"lossratio", default=0.0)

	def start_run(self, task):
		generic.Connection.start_run(self, task)
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
		host.execute("pidof tcpdump >/dev/null || (tcpdump -i dummy >/dev/null 2>&1 </dev/null &)", task)

	def stop_run(self, task):
		generic.Connection.stop_run(self, task)
		host = self.interface.device.host
		pipe_id = int(self.bridge_id) * 10
		host.execute("ipfw delete %d" % pipe_id, task)
		host.execute("ipfw pipe delete %d" % pipe_id, task)
		host.execute("ipfw delete %d" % ( pipe_id + 1 ), task)
			
	def prepare_run(self, task):
		host = self.interface.device.host
		host.execute("brctl addbr dummy", task)
		host.execute("ifconfig dummy 0.0.0.0 up", task)
		generic.Connection.prepare_run(self, task)

	def destroy_run(self, task):
		generic.Connection.destroy_run(self, task)

	def change_run(self, dom, task):
		self.decode_xml(dom)
		generic.Connection.start_run(self, task)
		host = self.interface.device.host
		pipe_id = int(self.bridge_id) * 10
		pipe_config=""
		if self.delay:
			pipe_config = pipe_config + " " + "delay %sms" % self.delay
		if self.bandwidth:
			pipe_config = pipe_config + " " + "bw %sk" % self.bandwidth
		host.execute("ipfw pipe %d config %s" % ( pipe_id, pipe_config ), task)
		host.execute("ipfw delete %d" % pipe_id, task)
		if self.lossratio:
			host.execute("ipfw add %d prob %s drop via %s out" % ( pipe_id, self.lossratio, self.bridge_name() ), task)
		self.save()