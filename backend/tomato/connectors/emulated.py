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
from tomato.lib import tc, tcpdump, tasks, ifaceutil
from tomato import fault

DEFAULT_CAPTURE_FILTER = ""
DEFAULT_CAPTURE_TO_FILE = False
DEFAULT_CAPTURE_VIA_NET = False

netemProperties = ["bandwidth", "delay", "jitter", "distribution", "lossratio", "lossratio_correlation", "duplicate", "corrupt"]
netemDefaults = {"bandwidth": 10000.0, "distribution": None}
netemValueConvert = {
	"bandwidth": lambda x: float(x if x else netemDefaults["bandwidth"]),
	"delay": lambda x: float(x if x else 0.0),
	"jitter": lambda x: float(x if x else 0.0),
	"delay_correlation": lambda x: float(x if x else 0.0),
	"distribution": lambda x: x if x in ["normal", "pareto", "paretonormal"] else None,
	"lossratio": lambda x: float(x if x else 0.0),
	"lossratio_correlation": lambda x: float(x if x else 0.0),
	"duplicate": lambda x: float(x if x else 0.0),
	"corrupt": lambda x: float(x if x else 0.0),	
}
netemValuesChecks = {
	"bandwidth": lambda x: x > 0.0,
	"delay": lambda x: x >= 0.0,
	"jitter": lambda x: x >= 0.0,
	"delay_correlation": lambda x: 0.0 <= x <= 100.0,
	"distribution": lambda x: x is None or x in ["normal", "pareto", "paretonormal"],
	"lossratio": lambda x: 0.0 <= x <= 100.0,
	"lossratio_correlation": lambda x: 0.0 <= x <= 100.0,
	"duplicate": lambda x: 0.0 <= x <= 100.0,
	"corrupt": lambda x: 0.0 <= x <= 100.0,
}

class EmulatedConnection(Connection):
	
	class Meta:
		db_table = "tomato_emulatedconnection"
		app_label = 'tomato'

	def init(self):
		self.attrs = {}
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
				
	def getNetemProp(self, prop, dir=None):
		if dir == "to":
			return self.getAttribute(prop+"_to", self.getNetemProp(prop))
		if dir == "from":
			return self.getAttribute(prop+"_from", self.getNetemProp(prop))
		return self.getAttribute(prop, netemDefaults.get(prop, 0.0))
				
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
		})
		for p in netemProperties:
			capabilities["configure"][p] = True
			capabilities["configure"][p+"_to"] = True
			capabilities["configure"][p+"_from"] = True
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
		for p in netemProperties:
			if p in properties:
				val = properties[p]
				val = netemValueConvert[p](val)
				fault.check(netemValuesChecks[p](val), "Invalid value for %s: %s", (p, val))
				self.setAttribute(p, val)
			if p + "_to" in properties:
				val = properties[p+"_to"]
				val = netemValueConvert[p](val)
				fault.check(netemValuesChecks[p](val), "Invalid value for %s: %s", (p+"_to", val))
				self.setAttribute(p+"_to", val)
			if p + "_from" in properties:
				val = properties[p+"_from"]
				val = netemValueConvert[p](val)
				fault.check(netemValuesChecks[p](val), "Invalid value for %s: %s", (p+"_from", val))
				self.setAttribute(p+"_from", val)
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
		assert not self.getAttribute("ifb_id", None) is None
		ifb = "ifb%d" % self.getAttribute("ifb_id", None)
		ifaceutil.ifup(host, ifb)
		tc.setLinkEmulation(host, iface, 
			bandwidth=self.getNetemProp("bandwidth", "to"),
			delay=self.getNetemProp("delay", "to"),
			jitter=self.getNetemProp("jitter", "to"),
			delay_correlation=self.getNetemProp("delay_correlation", "to"),
			distribution=self.getNetemProp("distribution", "to"),
			loss=self.getNetemProp("lossratio", "to"),
			loss_correlation=self.getNetemProp("lossratio_correlation", "to"),
			duplicate=self.getNetemProp("duplicate", "to"),
			corrupt=self.getNetemProp("corrupt", "to"),
		)
		tc.setLinkEmulation(host, ifb,
			bandwidth=self.getNetemProp("bandwidth", "from"),
			delay=self.getNetemProp("delay", "from"),
			jitter=self.getNetemProp("jitter", "from"),
			delay_correlation=self.getNetemProp("delay_correlation", "from"),
			distribution=self.getNetemProp("distribution", "from"),
			loss=self.getNetemProp("lossratio", "from"),
			loss_correlation=self.getNetemProp("lossratio_correlation", "from"),
			duplicate=self.getNetemProp("duplicate", "from"),
			corrupt=self.getNetemProp("corrupt", "from"),
		)
		tc.setIncomingRedirect(host, iface, ifb)
		
	def _captureName(self):
		return "capture-%d-%s-%s" % (self.connector.topology.id, self.interface.device.name, self.interface.name)
		
	def _assignIfb(self, ifb_id=None):
		if not ifb_id is None:
			self.setAttribute("ifb_id", ifb_id)
		if self.getAttribute("ifb_id") is None:
			host = self.getHost()
			host.takeId("ifb", self._assignIfb)
	
	def _unassignIfb(self):
		if not self.getAttribute("ifb_id") is None:
			host = self.getHost()
			ifb_id = self.getAttribute("ifb_id")
			self.deleteAttribute("ifb_id")
			host.giveId("ifb", ifb_id)
	
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
		assign_ifb = tasks.Task("assign-ifb", self._assignIfb)
		configure_link = tasks.Task("configure-link", self._configLink, after=assign_ifb)
		start_capture = tasks.Task("start-capture", self._startCapture)
		taskset.add([assign_ifb, configure_link, start_capture])
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

	def _unconfigLink(self):
		host = self.getHost()
		iface = self.internalInterface()
		bridge = self.getBridge()
		try:
			tc.clearIncomingRedirect(host, iface)
			tc.clearLinkEmulation(host, iface)
			tc.clearLinkEmulation(host, bridge)
		except:
			pass
	
	def getStopTasks(self):
		taskset = Connection.getStopTasks(self)
		unassign_ifb = tasks.Task("unassign-ifb", self._unassignIfb)
		unconfigure_link = tasks.Task("unconfigure-link", self._unconfigLink, after=unassign_ifb)
		stop_capture = tasks.Task("stop-capture", self._stopCapture)
		taskset.add([unassign_ifb, unconfigure_link, stop_capture])
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
		ifb_id = self.getAttribute("ifb_id", None)
		if not ifb_id is None:
			ids.update(ifb=set((ifb_id,)))
		return ids
