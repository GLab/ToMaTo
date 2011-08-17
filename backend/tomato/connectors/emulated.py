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
from tomato.lib import tc, tcpdump, tasks
from tomato import fault

DEFAULT_LOSSRATIO = 0.0
DEFAULT_DELAY = 0
DEFAULT_BANDWIDTH = 10000
DEFAULT_CAPTURE_FILTER = ""
DEFAULT_CAPTURE_TO_FILE = False
DEFAULT_CAPTURE_VIA_NET = False

class EmulatedConnection(Connection):
	
	class Meta:
		db_table = "tomato_emulatedconnection"
		app_label = 'tomato'

	def init(self):
		self.attrs = {}
		self.setBandwidth(DEFAULT_BANDWIDTH)
		self.setDelay(DEFAULT_DELAY)
		self.setLossRatio(DEFAULT_LOSSRATIO)
		self.setCaptureFilter("")
		self.setCaptureToFile(False)
		self.setCaptureViaNet(False)
	
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

	def getCaptureFilter(self):
		return self.getAttribute("capture_filter", DEFAULT_CAPTURE_FILTER)
	
	def setCaptureFilter(self, value):
		self.setAttribute("capture_filter", str(value))

	def getCaptureToFile(self):
		return self.getAttribute("capture_to_file", DEFAULT_CAPTURE_TO_FILE)
	
	def setCaptureToFile(self, value):
		self.setAttribute("capture_to_file", bool(value))

	def getCaptureViaNet(self):
		return self.getAttribute("capture_via_net", DEFAULT_CAPTURE_VIA_NET)
	
	def setCaptureViaNet(self, value):
		self.setAttribute("capture_via_net", bool(value))

	def getCapabilities(self, user):
		capabilities = Connection.getCapabilities(self, user)
		isUser = self.connector.topology.checkAccess(Permission.ROLE_USER, user)
		capabilities["configure"].update({
			"capture_filter": True,
			"capture_to_file": True,
			"capture_via_net": True,
			"delay": True,
			"bandwidth": True,
			"lossratio": True,
		})
		capabilities["action"].update({
			"download_capture": isUser and not self.connector.state == State.CREATED and self.getCaptureToFile()
		})
		capabilities["other"] = {
			"live_capture": isUser and self.connector.state == State.STARTED and self.getCaptureViaNet()
		}
		return capabilities

	def configure(self, properties):
		oldCaptureToFile = self.getCaptureToFile()
		oldCaptureViaNet = self.getCaptureViaNet()
		oldCaptureFilter = self.getCaptureFilter()
		#FIXME: validate filter
		if "capture_to_file" in properties:
			self.setCaptureToFile(properties["capture_to_file"])
		if "capture_filter" in properties:
			self.setCaptureFilter(properties["capture_filter"])
		if "capture_via_net" in properties:
			self.setCaptureViaNet(properties["capture_via_net"])
		if "delay" in properties:
			self.setDelay(properties["delay"])
		if "bandwidth" in properties:
			self.setBandwidth(properties["bandwidth"])
		if "lossratio" in properties:
			self.setLossRatio(properties["lossratio"])
		Connection.configure(self, properties)
		if self.connector.state == State.STARTED:
			self._configLink()
			if oldCaptureToFile and (not self.getCaptureToFile() or self.getCaptureFilter() != oldCaptureFilter):
				self._stopCaptureToFile()
			if oldCaptureViaNet and (not self.getCaptureViaNet() or self.getCaptureFilter() != oldCaptureFilter):
				self._stopCaptureViaNet()
			if self.getCaptureToFile() and (not oldCaptureToFile or self.getCaptureFilter() != oldCaptureFilter):
				self._startCaptureToFile()
			if self.getCaptureViaNet() and (not oldCaptureViaNet or self.getCaptureFilter() != oldCaptureFilter):
				self._startCaptureViaNet()
			
	def _configLink(self):
		host = self.getHost()
		iface = self.internalInterface()
		bridge = self.getBridge()
		tc.setLinkEmulation(host, iface, self.getBandwidth(), loss=self.getLossRatio(), delay=self.getDelay())
		tc.setLinkEmulation(host, bridge, self.getBandwidth(), loss=self.getLossRatio(), delay=self.getDelay())
		tc.setIncomingRedirect(host, iface, bridge)
		
	def _captureName(self):
		return "capture-%s-%s-%s" % (self.connector.topology.id, self.interface.device.name, self.interface.name)
		
	def _startCapture(self):
		if self.getCaptureToFile():
			self._startCaptureToFile()
		if self.getCaptureViaNet():
			self._startCaptureViaNet()

	def _startCaptureToFile(self):
		host = self.interface.device.host
		tcpdump.startCaptureToFile(host, self._captureName(), self.getBridge(), self.getCaptureFilter())

	def _setCapturePort(self, port):
		self.setAttribute("capture_port", port)

	def _startCaptureViaNet(self):
		host = self.interface.device.host
		port = self.getAttribute("capture_port", None)
		if not port:
			host.takeId("port", self._setCapturePort)
		port = self.getAttribute("capture_port")
		tcpdump.startCaptureViaNet(host, self._captureName(), port, self.getBridge(), self.getCaptureFilter())

	def getStartTasks(self):
		taskset = Connection.getStartTasks(self)
		configure_link = tasks.Task("configure-link", self._configLink)
		start_capture = tasks.Task("start-capture", self._startCapture)
		taskset.add([configure_link, start_capture])
		return taskset
	
	def _stopCapture(self):
		if self.getCaptureToFile():
			self._stopCaptureToFile()
		if self.getCaptureViaNet():
			self._stopCaptureViaNet()
			
	def _stopCaptureToFile(self):
		host = self.getHost()
		tcpdump.stopCaptureToFile(host, self._captureName())

	def _stopCaptureViaNet(self):
		host = self.getHost()
		port = self.getAttribute("capture_port")
		if host and port:
			tcpdump.stopCaptureViaNet(host, self._captureName(), port)
			self.deleteAttribute("capture_port")
			host.giveId("port", port)

	def getStopTasks(self):
		taskset = Connection.getStopTasks(self)
		stop_capture = tasks.Task("stop-capture", self._stopCapture)
		taskset.add([stop_capture])
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
		fault.check(not self.connector.state == State.CREATED and self.getCaptureToFile(), "Captures not ready")
		host = self.getHost()
		return tcpdump.downloadCaptureUri(host, self._captureName())
	
	def toDict(self, auth):
		res = Connection.toDict(self, auth)
		res["attrs"].update(self.getAttributes())
		if self.connector.state == State.STARTED and self.getCaptureViaNet():
			res["attrs"].update(capture_host=self.getHost().name)
		return res
	
	def getIdUsage(self, host):
		ids = Connection.getIdUsage(self, host)
		capture_port = self.getAttribute("capture_port", None)
		if capture_port:
			ids.update(port=set((capture_port,)))
		return ids
