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

import generic

from lib import ipfw, tcpdump, util

DEFAULT_LOSSRATIO = 0.0
DEFAULT_DELAY = 0
DEFAULT_BANDWIDTH = 10000
DEFAULT_CAPTURING = False

class EmulatedConnection(generic.Connection):
	
	def init(self):
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
		if "lossratio" in self.attributes:
			try:
				return float(self.attributes["lossratio"])
			except: #pylint: disable-msg=W0702
				return DEFAULT_LOSSRATIO
		return DEFAULT_LOSSRATIO
	
	def setLossRatio(self, value):
		self.attributes["lossratio", str(float(value))]
	
	def getDelay(self):
		if "delay" in self.attributes:
			try:
				return int(self.attributes["delay"])
			except: #pylint: disable-msg=W0702
				return DEFAULT_DELAY
		return DEFAULT_DELAY 
		
	def setDelay(self, value):
		self.attributes["delay", str(int(value))]

	def getBandwidth(self):
		if "bandwidth" in self.attributes:
			try:
				return int(self.attributes["bandwidth"])
			except:
				return DEFAULT_BANDWIDTH
		return DEFAULT_BANDWIDTH
				
	def setBandwidth(self, value):
		self.attributes["bandwidth", str(int(value))]

	def getCapturing(self):
		if "capture" in self.attributes:
			try:
				return util.parse_bool(self.attributes["capture"])
			except:
				return DEFAULT_CAPTURING
		return DEFAULT_CAPTURING
	
	def setCapturing(self, value):
		self.attributes["capture", str(bool(value))]

	def configure(self, properties):
		oldCapturing = self.getCapturing()
		generic.Connection.configure(self, properties)
		if self.connector.state == generic.State.STARTED:
			self._configLink()
			if oldCapturing and not self.getCapturing():
				self._stopCapture()
			if self.getCapturing() and not oldCapturing:
				self._startCapture()
			
	def getHost(self):
		host = self.interface.device.host
		assert host
		return host
			
	def _configLink(self):
		pipe_id = int(self.bridgeId())
		host = self.getHost()
		ipfw.configurePipe(host, pipe_id, delay=self.getDelay(), bandwidth=self.getBandwidth(), lossratio=self.getLossRatio())
		
	def _captureName(self):
		return "%s-%s-%s" % (self.connector.topology.name, self.connector.name, self)
		
	def _startCapture(self):
		host = self.interface.device.host
		tcpdump.startCapture(host, self._captureName(), self.bridgeName())

	def _createPipe(self):
		pipe_id = int(self.bridgeId())
		host = self.getHost()
		ipfw.loadModule(host)
		ipfw.createPipe(host, pipe_id, self.bridgeName(), dir="out")

	def getStartTasks(self):
		from lib import tasks
		taskset = generic.Connection.getStartTasks(self)
		taskset.addTask(tasks.Task("create-pipe", self._createPipe))
		taskset.addTask(tasks.Task("configure-link", self._configLink, depends="configure-link"))
		if self.getCapturing():
			taskset.addTask(tasks.Task("start-capture", self._startCapture))
		return taskset
	
	def _stopCapture(self):
		host = self.getHost()
		tcpdump.stopCapture(host, self._captureName())

	def _deletePipes(self):
		ipfw.deletePipe(self.getHost(), int(self.bridgeId()))

	def getStopTasks(self):
		from lib import tasks
		taskset = generic.Connection.getStopTasks(self)
		if "bridgeId" in self.attributes:
			taskset.addTask(tasks.Task("delete-pipes", self._deletePipes))
		if self.getCapturing():
			taskset.addTask(tasks.Task("stop-capture", self._stopCapture))
		return taskset
	
	def getPrepareTasks(self):
		return generic.Connection.getPrepareTasks(self)

	def _removeCaptureDir(self):
		host = self.getHost()
		if host:
			tcpdump.removeCapture(host, self._captureName())
		
	def getDestroyTasks(self):
		from lib import tasks
		taskset = generic.Connection.getDestroyTasks(self)
		taskset.addTask(tasks.Task("remove-capture-dir", self._removeCaptureDir))
		return taskset

	def downloadSupported(self):
		return not self.connector.state == generic.State.CREATED and self.getCapturing()

	def downloadCaptureUri(self):
		host = self.getHost()
		return tcpdump.downloadCaptureUri(host, self._captureName())
	
	def toDict(self, auth):
		res = generic.Connection.toDict(self, auth)		
		return res
	