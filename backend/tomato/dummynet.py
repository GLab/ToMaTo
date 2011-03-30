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
import generic, util

class EmulatedConnection(generic.Connection):
	
	class Meta:
		abstract = True
	
	def upcast(self):
		if self.is_tinc():
			return self.tincconnection # pylint: disable-msg=E1101
		return self

	def is_tinc(self):
		try:
			self.tincconnection # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False
				
	def configure(self, properties, task):
		old_capture = self.attributes["capture"]
		generic.Connection.configure(self, properties, task)
		if self.connector.state == generic.State.STARTED:
			self._config_link(task)
			if old_capture and not self.attributes.get("capture"):
				self._stop_capture(task)
			if self.attributes.get("capture") and not old_capture:
				self._start_capture(task)
			
	def _config_link(self, task):
		host = self.interface.device.host
		pipe_id = int(self.bridge_id) * 10
		pipe_config=""
		if "delay" in self.attributes:
			try:
				delay = int(self.attributes["delay"])
			except: #pylint: disable-msg=W0702
				delay = 0
			pipe_config = pipe_config + " " + "delay %sms" % delay
		if "bandwidth" in self.attributes:		
			try:
				bandwidth = int(self.attributes["bandwidth"])			
			except: #pylint: disable-msg=W0702
				bandwidth = 10000
			pipe_config = pipe_config + " " + "bw %sk" % bandwidth
		if "lossratio" in self.attributes:
			try:
				lossratio = float(self.attributes["lossratio"])
			except: #pylint: disable-msg=W0702
				lossratio = 0.0
			pipe_config = pipe_config + " " + "plr %s" % lossratio
		host.execute("ipfw pipe %d config %s" % ( pipe_id, pipe_config ), task)
		
	def _capture_dir(self):
		return "%s/captures-%s" % ( self.connector.topology.get_remote_control_dir(), self.id ) # pylint: disable-msg=E1101

	def _start_capture(self, task):
		host = self.interface.device.host
		directory = self._capture_dir()
		host.execute("mkdir -p %s" % directory, task )
		host.bridge_create(self.bridge_name())
		host.execute("ip link set up %s" % self.bridge_name(), task)
		host.execute("tcpdump -i %s -n -C 10 -w %s/capture -W 5 -s0 >/dev/null 2>&1 </dev/null & echo $! > %s.pid" % ( self.bridge_name(), directory, directory ), task )		

	def start_run(self, task):
		generic.Connection.start_run(self, task)
		host = self.interface.device.host
		if not host:
			import fault
			raise fault.new(fault.INVALID_TOPOLOGY_STATE_TRANSITION, "Cannot start dummynet, device must be created first: %s" % self.interface.device)
		pipe_id = int(self.bridge_id()) * 10
		host.execute("modprobe ipfw_mod", task)
		host.execute("ipfw add %d pipe %d via %s out" % ( pipe_id, pipe_id, self.bridge_name() ), task)
		self._config_link(task)
		host.execute("pidof tcpdump >/dev/null || (tcpdump -i dummy >/dev/null 2>&1 </dev/null &)", task)
		if "capture" in self.attributes:
			self._start_capture(task)

	def _stop_capture(self, task):
		host = self.interface.device.host
		directory = self._capture_dir()
		host.execute("cat %s.pid | xargs -r kill" % directory, task )
		host.execute("rm %s.pid" % directory, task )

	def stop_run(self, task):
		generic.Connection.stop_run(self, task)
		host = self.interface.device.host
		if "bridge_id" in self.attributes:
			pipe_id = int(self.bridge_id()) * 10
			host.execute("ipfw delete %d" % pipe_id, task)
			host.execute("ipfw pipe delete %d" % pipe_id, task)
			host.execute("ipfw delete %d" % ( pipe_id + 1 ), task)
		if "capture" in self.attributes:
			self._stop_capture(task)

	def prepare_run(self, task):
		host = self.interface.device.host
		host.bridge_create("dummy")
		host.execute("ifconfig dummy 0.0.0.0 up", task)
		generic.Connection.prepare_run(self, task)

	def destroy_run(self, task):
		generic.Connection.destroy_run(self, task)
		host = self.interface.device.host
		directory = self._capture_dir()
		if host:
			host.execute("rm -r %s %s.pid" % (directory, directory), task )

	def download_supported(self):
		return not self.connector.state == generic.State.CREATED and "capture" in self.attributes

	def download_capture_uri(self):
		filename = "%s_%s_%s.tar.gz" % (self.connector, self.interface, uuid.uuid1())
		host = self.interface.device.host
		path = "%s/%s" % (host.hostserver_basedir, filename)
		host.execute("tar -czf %s -C %s . " % ( path, self._capture_dir() ) )
		return host.download_grant(filename, filename)
	
	def to_dict(self, auth):
		res = generic.Connection.to_dict(self, auth)		
		return res
	