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

from tomato.connectors import Connection
from tomato.generic import State
from tomato.topology import Permission
from tomato.lib import ipfw, tcpdump, tasks
from tomato import fault

DEFAULT_LOSSRATIO = 0.0
DEFAULT_DELAY = 0
DEFAULT_BANDWIDTH = 10000
DEFAULT_CAPTURING = False

class EmulatedConnection(Connection):
	
	class Meta:
		db_table = "tomato_emulatedconnection"
		app_label = 'tomato'

	def init(self):
		self.attrs = {}
		self.setBandwidth(DEFAULT_BANDWIDTH)
		self.setDelay(DEFAULT_DELAY)
		self.setLossRatio(DEFAULT_LOSSRATIO)
	
	def upcast(self):
		if self.isTinc():
			return self.tincconnection # pylint: disable-msg=E1101
		return self

	def isTinc(self):
		try:
			self.tincconnection # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False
				
	def getLossRatio(self):
		return self.getAttribute("lossratio", DEFAULT_LOSSRATIO)
	
	def setLossRatio(self, value):
		self.setAttribute("lossratio", float(value))
	
	def getDelay(self):
		return self.getAttribute("delay", DEFAULT_DELAY)
		
	def setDelay(self, value):
		self.setAttribute("delay", int(value))

	def getBandwidth(self):
		return self.getAttribute("bandwidth", DEFAULT_BANDWIDTH)
				
	def setBandwidth(self, value):
		self.setAttribute("bandwidth", int(value))

	def getCapturing(self):
		return self.getAttribute("capture", DEFAULT_CAPTURING)
	
	def setCapturing(self, value):
		self.setAttribute("capture", bool(value))

	def getCapabilities(self, user):
		capabilities = Connection.getCapabilities(self, user)
		isUser = self.connector.topology.checkAccess(Permission.ROLE_USER, user)
		capabilities["configure"].update({
			"capture": True,
			"delay": True,
			"bandwidth": True,
			"lossratio": True,
		})
		capabilities["action"].update({
			"download_capture": isUser and not self.connector.state == State.CREATED and self.getCapturing()
		})
		return capabilities

	def configure(self, properties):
		oldCapturing = self.getCapturing()
		if "capture" in properties:
			self.setCapturing(properties["capture"])
		if "delay" in properties:
			self.setDelay(properties["delay"])
		if "bandwidth" in properties:
			self.setBandwidth(properties["bandwidth"])
		if "lossratio" in properties:
			self.setLossRatio(properties["lossratio"])
		Connection.configure(self, properties)
		if self.connector.state == State.STARTED:
			self._configLink()
			if oldCapturing and not self.getCapturing():
				self._stopCapture()
			if self.getCapturing() and not oldCapturing:
				self._startCapture()
			
	def _configLink(self):
		pipe_id = int(self.getBridgeId())
		host = self.getHost()
		ipfw.configurePipe(host, pipe_id, delay=self.getDelay(), bandwidth=self.getBandwidth(), lossratio=self.getLossRatio())
		
	def _captureName(self):
		return "%s-%s-%s" % (self.connector.topology.name, self.connector.name, self)
		
	def _startCapture(self):
		if self.getCapturing():
			host = self.interface.device.host
			tcpdump.startCapture(host, self._captureName(), self.getBridge())

	def _createPipe(self):
		pipe_id = int(self.getBridgeId())
		host = self.getHost()
		ipfw.loadModule(host)
		# in router mode ipfw is only triggered once, but for other modes twice		
		dir="" if self.connector.type == "router" else "out"
		ipfw.createPipe(host, pipe_id, self.getBridge(), dir=dir)

	def getStartTasks(self):
		taskset = Connection.getStartTasks(self)
		create_pipe = tasks.Task("create-pipe", self._createPipe)
		configure_link = tasks.Task("configure-link", self._configLink, after=create_pipe)
		start_capture = tasks.Task("start-capture", self._startCapture)
		taskset.add([create_pipe, configure_link, start_capture])
		return taskset
	
	def _stopCapture(self):
		if self.getCapturing():
			host = self.getHost()
			tcpdump.stopCapture(host, self._captureName())

	def _deletePipes(self):
		if self.bridge_id:
			ipfw.deletePipe(self.getHost(), int(self.bridge_id))

	def getStopTasks(self):
		taskset = Connection.getStopTasks(self)
		delete_pipes = tasks.Task("delete-pipes", self._deletePipes)
		stop_capture = tasks.Task("stop-capture", self._stopCapture)
		taskset.add([delete_pipes, stop_capture])
		return taskset
	
	def getPrepareTasks(self):
		return Connection.getPrepareTasks(self)

	def _removeCaptureDir(self):
		host = self.getHost()
		if host:
			tcpdump.removeCapture(host, self._captureName())
		
	def getDestroyTasks(self):
		taskset = Connection.getDestroyTasks(self)
		taskset.add(tasks.Task("remove-capture-dir", self._removeCaptureDir))
		return taskset

	def downloadCaptureUri(self):
		fault.check(not self.connector.state == State.CREATED and self.getCapturing(), "Captures not ready")
		host = self.getHost()
		return tcpdump.downloadCaptureUri(host, self._captureName())
	
	def toDict(self, auth):
		res = Connection.toDict(self, auth)
		res["attrs"].update(self.getAttributes())		
		return res
	
