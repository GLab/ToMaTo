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
	
	def init(self):
		self.attributes["lossratio"] = "0.0"
		self.attributes["delay"] = "0"
		self.attributes["bandwidth"] = "10000"
	
	def _ipfw(self, cmd):
		self.interface.device.host.execute("ipfw %s" % cmd)
		
	
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
				
	def configure(self, properties):
		old_capture = self.attributes["capture"]
		generic.Connection.configure(self, properties)
		if self.connector.state == generic.State.STARTED:
			self._config_link()
			if old_capture and not self.attributes.get("capture"):
				self._stop_capture()
			if self.attributes.get("capture") and not old_capture:
				self._start_capture()
			
	def _config_link(self):
		pipe_id = int(self.bridge_id()) * 10
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
		self._ipfw("pipe %d config %s" % ( pipe_id, pipe_config ))
		
	def _capture_dir(self):
		return "%s/captures-%s" % ( self.connector.topology.get_remote_control_dir(), self.id ) # pylint: disable-msg=E1101

	def _start_capture(self):
		host = self.interface.device.host
		directory = self._capture_dir()
		host.file_mkdir(directory)
		host.bridge_create(self.bridge_name())
		host.execute("ip link set up %s" % self.bridge_name())
		host.execute("tcpdump -i %s -n -C 10 -w %s/capture -W 5 -s0 >/dev/null 2>&1 </dev/null & echo $! > %s.pid" % ( self.bridge_name(), directory, directory ))		

	def _load_ipfw_module(self):
		self.interface.device.host.execute("modprobe ipfw_mod")

	def _create_pipe(self):
		pipe_id = int(self.bridge_id()) * 10
		self._ipfw("add %d pipe %d via %s out" % ( pipe_id, pipe_id, self.bridge_name() ))		

	def _ensure_tcpdump_running(self):
		host = self.interface.device.host
		host.execute("pidof tcpdump >/dev/null || (tcpdump -i dummy >/dev/null 2>&1 </dev/null &)")

	def get_start_tasks(self):
		import tasks
		taskset = generic.Connection.get_start_tasks(self)
		taskset.addTask(tasks.Task("load-ipfw-module", self._load_ipfw_module))
		taskset.addTask(tasks.Task("create-pipe", self._create_pipe, depends="load-ipfw-module"))
		taskset.addTask(tasks.Task("configure-link", self._config_link, depends="create-pipe"))
		if util.parse_bool(self.attributes["capture"]):
			taskset.addTask(tasks.Task("start-capture", self._start_capture))
		else:
			taskset.addTask(tasks.Task("ensure-tcpdump-running", self._ensure_tcpdump_running))
		return taskset
	
	def _stop_capture(self):
		host = self.interface.device.host
		directory = self._capture_dir()
		host.process_kill("%s.pid" % directory)

	def _delete_pipes(self):
		pipe_id = int(self.bridge_id()) * 10
		self._ipfw("delete %d" % pipe_id)
		self._ipfw("pipe delete %d" % pipe_id)
		self._ipfw("delete %d" % ( pipe_id + 1 ))		

	def get_stop_tasks(self):
		import tasks
		taskset = generic.Connection.get_stop_tasks(self)
		if "bridge_id" in self.attributes:
			taskset.addTask(tasks.Task("delete-pipes", self._delete_pipes))
		if util.parse_bool(self.attributes["capture"]):
			taskset.addTask(tasks.Task("stop-capture", self._stop_capture))
		return taskset
	
	def _create_dummy_bridge(self):
		host = self.interface.device.host
		host.bridge_create("dummy")
		host.execute("ifconfig dummy 0.0.0.0 up")

	def get_prepare_taskset(self):
		import tasks
		taskset = generic.Connection.get_prepare_tasks(self)
		taskset.addTask(tasks.Task("create-dummy-bridge", self._create_dummy_bridge))
		return taskset

	def _remove_capture_dir(self):
		host = self.interface.device.host
		directory = self._capture_dir()
		if host:
			host.file_delete(directory, recursive=True)
		
	def get_destroy_tasks(self):
		import tasks
		taskset = generic.Connection.get_destroy_tasks(self)
		taskset.addTask(tasks.Task("remove-capture-dir", self._remove_capture_dir))
		return taskset

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
	