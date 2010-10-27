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

import uuid
import generic, hosts, util

class EmulatedConnection(generic.Connection):
	delay = models.IntegerField(null=True)
	bandwidth = models.IntegerField(null=True)
	lossratio = models.FloatField(null=True)
	capture = models.BooleanField(default=False)
	
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
		if self.capture:
			dom.setAttribute("capture", str(self.capture))
				
	def decode_xml(self, dom):
		generic.Connection.decode_xml(self, dom)
		try:
			self.delay = int(util.get_attr(dom, "delay", default="0"))
		except:
			self.delay = 0
		try:
			self.bandwidth = int(util.get_attr(dom, "bandwidth", default="0"))			
		except:
			self.bandwidth = 10000
		try:
			self.lossratio = float(util.get_attr(dom,"lossratio", default=0.0))
		except:
			self.lossratio = 0.0
		self.capture = util.parse_bool(util.get_attr(dom, "capture", default="false"))

	def _config_link(self, task):
		host = self.interface.device.host
		pipe_id = int(self.bridge_id) * 10
		pipe_config=""
		if self.delay:
			pipe_config = pipe_config + " " + "delay %sms" % self.delay
		if self.bandwidth:
			pipe_config = pipe_config + " " + "bw %sk" % self.bandwidth
		if self.lossratio:
			pipe_config = pipe_config + " " + "plr %s" % self.lossratio
		host.execute("ipfw pipe %d config %s" % ( pipe_id, pipe_config ), task)

	def _capture_dir(self):
		return "%s/captures-%s" % ( self.connector.topology.get_remote_control_dir(), self.id )

	def _start_capture(self, task):
		host = self.interface.device.host
		dir = self._capture_dir()
		host.execute("mkdir -p %s" % dir, task )
		host.bridge_create(self.bridge_name())
		host.execute("ip link set up %s" % self.bridge_name(), task)
		host.execute("tcpdump -i %s -n -C 10 -w %s/capture -W 5 -s0 >/dev/null 2>&1 </dev/null & echo $! > %s.pid" % ( self.bridge_name(), dir, dir ), task )		

	def start_run(self, task):
		generic.Connection.start_run(self, task)
		host = self.interface.device.host
		pipe_id = int(self.bridge_id) * 10
		host.execute("modprobe ipfw_mod", task)
		host.execute("ipfw add %d pipe %d via %s out" % ( pipe_id, pipe_id, self.bridge_name() ), task)
		self._config_link(task)
		host.execute("pidof tcpdump >/dev/null || (tcpdump -i dummy >/dev/null 2>&1 </dev/null &)", task)
		if self.capture:
			self._start_capture(task)

	def _stop_capture(self, task):
		host = self.interface.device.host
		dir = self._capture_dir()
		host.execute("cat %s.pid | xargs -r kill" % dir, task )
		host.execute("rm %s.pid" % dir, task )

	def stop_run(self, task):
		generic.Connection.stop_run(self, task)
		host = self.interface.device.host
		if self.bridge_id:
			pipe_id = int(self.bridge_id) * 10
			host.execute("ipfw delete %d" % pipe_id, task)
			host.execute("ipfw pipe delete %d" % pipe_id, task)
			host.execute("ipfw delete %d" % ( pipe_id + 1 ), task)
		if self.capture:
			self._stop_capture(task)
			
	def prepare_run(self, task):
		host = self.interface.device.host
		host.bridge_create("dummy")
		host.execute("ifconfig dummy 0.0.0.0 up", task)
		generic.Connection.prepare_run(self, task)

	def destroy_run(self, task):
		generic.Connection.destroy_run(self, task)
		host = self.interface.device.host
		dir = self._capture_dir()
		if host:
			host.execute("rm -r %s %s.pid" % (dir, dir), task )

	def download_supported(self):
		return not self.connector.state == generic.State.CREATED and self.capture

	def download_capture(self):
		tmp_id = uuid.uuid1()
		filename = "/tmp/glabnetman-%s" % tmp_id
		host = self.interface.device.host
		host.execute("tar -czf %s -C %s . " % ( filename, self._capture_dir() ) )
		host.download("%s" % filename, filename)
		host.execute("rm %s" % filename)
		return filename

	def change_run(self, dom, task):
		cap = self.capture		
		self.decode_xml(dom)
		if self.connector.state == generic.State.STARTED:
			generic.Connection.start_run(self, task)
			self._config_link(task)
			if cap and not self.capture:
				self._stop_capture(task)
			if self.capture and not cap:
				self._start_capture(task)
		self.save()
