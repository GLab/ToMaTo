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

from .. import connections, config
from ..lib import cmd #@UnresolvedImport
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib.cmd import tc, net, process, path, fileserver #@UnresolvedImport
from ..lib.error import UserError

import os

DOC="""
	Description
	"""

ST_CREATED = "created"
ST_STARTED = "started"

class Bridge(connections.Connection):
	bridge_attr = Attr("bridge", type="str")
	bridge = bridge_attr.attribute()
	
	emulation_attr = Attr("emulation", desc="Enable emulation", type="bool", default=True)
	emulation = emulation_attr.attribute()

	bandwidth_to_attr = Attr("bandwidth_to", desc="Bandwidth", unit="kbit/s", type="float", minValue=0, maxValue=1000000, default=10000)
	bandwidth_to = bandwidth_to_attr.attribute()
	bandwidth_from_attr = Attr("bandwidth_from", desc="Bandwidth", unit="kbit/s", type="float", minValue=0, maxValue=1000000, default=10000)
	bandwidth_from = bandwidth_from_attr.attribute()

	lossratio_to_attr = Attr("lossratio_to", desc="Loss ratio", unit="%", type="float", minValue=0.0, maxValue=100.0, default=0.0)
	lossratio_to = lossratio_to_attr.attribute()
	lossratio_from_attr = Attr("lossratio_from", desc="Loss ratio", unit="%", type="float", minValue=0.0, maxValue=100.0, default=0.0)
	lossratio_from = lossratio_from_attr.attribute()
	
	duplicate_to_attr = Attr("duplicate_to", desc="Duplication ratio", unit="%", type="float", minValue=0.0, maxValue=100.0, default=0.0)
	duplicate_to = duplicate_to_attr.attribute()
	duplicate_from_attr = Attr("duplicate_from", desc="Duplication ratio", unit="%", type="float", minValue=0.0, maxValue=100.0, default=0.0)
	duplicate_from = duplicate_from_attr.attribute()

	corrupt_to_attr = Attr("corrupt_to", desc="Corruption ratio", unit="%", type="float", minValue=0.0, maxValue=100.0, default=0.0)
	corrupt_to = corrupt_to_attr.attribute()
	corrupt_from_attr = Attr("corrupt_from", desc="Corruption ratio", unit="%", type="float", minValue=0.0, maxValue=100.0, default=0.0)
	corrupt_from = corrupt_from_attr.attribute()

	delay_to_attr = Attr("delay_to", desc="Delay", unit="ms", type="float", minValue=0.0, default=0.0)
	delay_to = delay_to_attr.attribute()
	delay_from_attr = Attr("delay_from", desc="Delay", unit="ms", type="float", minValue=0.0, default=0.0)
	delay_from = delay_from_attr.attribute()

	jitter_to_attr = Attr("jitter_to", desc="Jitter", unit="ms", type="float", minValue=0.0, default=0.0)
	jitter_to = jitter_to_attr.attribute()
	jitter_from_attr = Attr("jitter_from", desc="Jitter", unit="ms", type="float", minValue=0.0, default=0.0)
	jitter_from = jitter_from_attr.attribute()

	distribution_to_attr = Attr("distribution_to", desc="Distribution", type="str", options={"uniform": "Uniform", "normal": "Normal", "pareto": "Pareto", "paretonormal": "Pareto-Normal"}, default="uniform")
	distribution_to = distribution_to_attr.attribute()
	distribution_from_attr = Attr("distribution_from", desc="Distribution", type="str", options={"uniform": "Uniform", "normal": "Normal", "pareto": "Pareto", "paretonormal": "Pareto-Normal"}, default="uniform")
	distribution_from = distribution_from_attr.attribute()
	

	capturing_attr = Attr("capturing", desc="Enable packet capturing", type="bool", default=False)
	capturing = capturing_attr.attribute()
	capture_filter_attr = Attr("capture_filter", desc="Packet filter expression", type="str", default="")
	capture_filter = capture_filter_attr.attribute()
	capture_port_attr = Attr("capture_port", type="int")
	capture_port = capture_port_attr.attribute()
	capture_mode_attr = Attr("capture_mode", desc="Capture mode", type="str", options={"net": "Via network", "file": "For download"}, default="file")
	capture_mode = capture_mode_attr.attribute()
	capture_pid_attr = Attr("capture_pid", type="int")
	capture_pid = capture_pid_attr.attribute()

	TYPE = "bridge"
	CAP_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		connections.REMOVE_ACTION: [ST_CREATED, ST_STARTED],
	}
	CAP_NEXT_STATE = {
		"start": ST_STARTED,
		"stop": ST_CREATED,
	}
	CAP_ACTIONS_EMUL = {
	}
	CAP_ACTIONS_CAPTURE = {
		"download_grant": [ST_CREATED, ST_STARTED],
	}
	CAP_ATTRS = {}
	CAP_ATTRS_EMUL = {
		"emulation": emulation_attr,
		"delay_to": delay_to_attr,
		"delay_from": delay_from_attr,
		"jitter_to": jitter_to_attr,
		"jitter_from": jitter_from_attr,
		"distribution_to": distribution_to_attr,
		"distribution_from": distribution_from_attr,
		"bandwidth_to": bandwidth_to_attr,
		"bandwidth_from": bandwidth_from_attr,
		"lossratio_to": lossratio_to_attr,
		"lossratio_from": lossratio_from_attr,
		"duplicate_to": duplicate_to_attr,
		"duplicate_from": duplicate_from_attr,
		"corrupt_to": corrupt_to_attr,
		"corrupt_from": corrupt_from_attr,
	}
	CAP_ATTRS_CAPTURE = {
		"capturing": capturing_attr,
		"capture_filter": capture_filter_attr,
		"capture_mode": capture_mode_attr,
	}
	DEFAULT_ATTRS = {"bandwidth_to": 10000, "bandwidth_from": 10000}
	CAP_CON_CONCEPTS = [(connections.CONCEPT_INTERFACE, connections.CONCEPT_INTERFACE)]
	DOC = DOC
	__doc__ = DOC #@ReservedAssignment
	
	class Meta:
		db_table = "tomato_bridge"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		connections.Connection.init(self, *args, **kwargs) #no id and no attrs before this line
		self.bridge = "br%d" % self.id
		self.capture_port = self.getResource("port")
				
	def _startCapturing(self):
		if not self.capturing or self.state == ST_CREATED:
			return
		if self.capture_mode == "file":
			if not os.path.exists(self.dataPath("capture")):
				os.mkdir(self.dataPath("capture"))
			self.capture_pid = cmd.spawn(["tcpdump", "-i", self.bridge, "-n", "-C", "10", "-w", self.dataPath("capture/"), "-U", "-W", "5", "-s0", self.capture_filter])
		elif self.capture_mode == "net":
			self.capture_pid = cmd.spawn(["tcpserver", "-qHRl", "0", "0", str(self.capture_port), "tcpdump", "-i", self.bridge, "-s0", "-nUw", "-", self.capture_filter])
		else:
			raise UserError(code=UserError.INVALID_CONFIGURATION, message="Capture mode must be either file or net")
				
	def _stopCapturing(self):
		if not self.capturing or self.state == ST_CREATED:
			return
		if self.capture_pid:
			process.kill(self.capture_pid)
			del self.capture_pid

	def modify_capturing(self, val):
		if self.capturing == val:
			return
		self.capturing = val
		if self.capturing:
			self._startCapturing()
		if not self.capturing:
			self._stopCapturing()
	
	def modify_capture_mode(self, val):
		self._captureRestart |= self.capture_mode != val
		self.capture_mode = val
	
	def modify_capture_filter(self, val):
		self._captureRestart |= self.capture_filter != val
		self.capture_filter = val
	
	def _startEmulation(self):
		if not self.emulation:
			return
		els = self.getElements()
		if len(els) != 2:
			return
		elA, elB = [el for el in els]
		if elA.id > elB.id:
			#force ordering on connected elements, so from and to have defined meanings
			#lower number is A, higher number is B, A -> B is FROM, B -> A is TO
			elA, elB = elB, elA
		ifA, ifB = elA.interfaceName(), elB.interfaceName()
		if not ifA or not ifB:
			return
		#set attributes in reversed manner as it only applies to traffic being received
		attrsA = dict([(k.replace("_to", ""), v) for k, v in self.attrs.iteritems() if k.endswith("_to")])
		attrsB = dict([(k.replace("_from", ""), v) for k, v in self.attrs.iteritems() if k.endswith("_from")])
		tc.setLinkEmulation(ifA, **attrsA)
		tc.setLinkEmulation(ifB, **attrsB)
	
	def _stopEmulation(self):
		els = self.getElements()
		if len(els) != 2:
			return
		ifA, ifB = [el.interfaceName() for el in els]
		if not ifA or not ifB:
			return
		try:
			tc.clearLinkEmulation(ifA)
		except:
			pass
		try:
			tc.clearLinkEmulation(ifB)
		except:
			pass
	
	def modify_emulation(self, val):
		if self.emulation == val:
			return
		self.emulation = val
		if self.emulation:
			self._startEmulation()
		if not self.emulation:
			self._stopEmulation()

	def modify_bandwidth_to(self, val):
		self._emulRestart |= self.bandwidth_to != val
		self.bandwidth_to = val

	def modify_bandwidth_from(self, val):
		self._emulRestart |= self.bandwidth_from != val
		self.bandwidth_from = val

	def modify_delay_to(self, val):
		self._emulRestart |= self.delay_to != val
		self.delay_to = val

	def modify_delay_from(self, val):
		self._emulRestart |= self.delay_from != val
		self.delay_from = val

	def modify_jitter_to(self, val):
		self._emulRestart |= self.jitter_to != val
		self.jitter_to = val

	def modify_jitter_from(self, val):
		self._emulRestart |= self.jitter_from != val
		self.jitter_from = val

	def modify_distribution_to(self, val):
		self._emulRestart |= self.distribution_to != val
		self.distribution_to = val

	def modify_distribution_from(self, val):
		self._emulRestart |= self.distribution_from != val
		self.distribution_from = val

	def modify_lossratio_to(self, val):
		self._emulRestart |= self.lossratio_to != val
		self.lossratio_to = val

	def modify_lossratio_from(self, val):
		self._emulRestart |= self.lossratio_from != val
		self.lossratio_from = val

	def modify_duplicate_to(self, val):
		self._emulRestart |= self.duplicate_to != val
		self.duplicate_to = val

	def modify_duplicate_from(self, val):
		self._emulRestart |= self.duplicate_from != val
		self.duplicate_from = val

	def modify_corrupt_to(self, val):
		self._emulRestart |= self.corrupt_to != val
		self.corrupt_to = val

	def modify_corrupt_from(self, val):
		self._emulRestart |= self.corrupt_from != val
		self.corrupt_from = val

	def modify(self, attrs):
		self._emulRestart = False
		self._captureRestart = False
		connections.Connection.modify(self, attrs)
		if self._emulRestart:
			# no need to stop emulation
			self._startEmulation()
		if self._captureRestart:
			self._stopCapturing()
			self._startCapturing()
		del self._emulRestart
		del self._captureRestart
	
	def action_start(self):
		net.bridgeCreate(self.bridge)
		net.ifUp(self.bridge)
		self.setState(ST_STARTED)
		self._startCapturing()
		for el in self.getElements():
			ifname = el.interfaceName()
			if ifname:
				self.connectInterface(ifname)
				
	def action_stop(self):
		for el in self.getElements():
			ifname = el.interfaceName()
			if ifname:
				self.disconnectInterface(ifname)
		self._stopCapturing()
		if net.bridgeExists(self.bridge):
			net.ifDown(self.bridge)
			net.bridgeRemove(self.bridge)
		self.setState(ST_CREATED)

	def remove(self):
		self.action_stop()
		connections.Connection.remove(self)

	def connectInterface(self, ifname):
		if self.state == ST_CREATED:
			return
		oldBridge = net.interfaceBridge(ifname)
		if oldBridge == self.bridge:
			return
		if oldBridge:
			net.bridgeRemoveInterface(oldBridge, ifname)
		net.bridgeAddInterface(self.bridge, ifname)
		if len(net.bridgeInterfaces(self.bridge)) == 2:
			self._startEmulation()
			# now elements are connected
			for el in self.getElements():
				el.onConnected()
	
	def disconnectInterface(self, ifname):
		if self.state == ST_CREATED:
			return
		if not net.bridgeExists(self.bridge):
			return
		if not ifname in net.bridgeInterfaces(self.bridge):
			return
		if len(net.bridgeInterfaces(self.bridge)) == 2:
			# now elements are no longer connected
			for el in self.getElements():
				el.onDisconnected()
			self._stopEmulation()
		net.bridgeRemoveInterface(self.bridge, ifname)

	def action_download_grant(self, limitSize=None):
		UserError.check(os.path.exists(self.dataPath("capture")), UserError.NO_DATA_AVAILABLE, "Nothing captured so far")
		entries = [os.path.join(self.dataPath("capture"), f) for f in path.entries(self.dataPath("capture"))]
		UserError.check(entries, UserError.NO_DATA_AVAILABLE, "Nothing captured so far")
		net.tcpslice(self.dataPath("capture.pcap"), entries, limitSize)
		return fileserver.addGrant(self.dataPath("capture.pcap"), fileserver.ACTION_DOWNLOAD, repeated=True)
		
	def upcast(self):
		return self

	def info(self):
		info = connections.Connection.info(self)
		return info
	
	def updateUsage(self, usage, data):
		if net.bridgeExists(self.bridge):
			traffic = sum(net.trafficInfo(self.bridge))
			usage.updateContinuous("traffic", traffic, data)
		if self.capture_pid and process.exists(self.capture_pid):
			cputime = process.cputime(self.capture_pid)
			usage.updateContinuous("cputime", cputime, data)
			usage.memory = process.memory(self.capture_pid)
		usage.diskspace = path.diskspace(self.dataPath())

if not config.MAINTENANCE:
	bridgeUtilsVersion = cmd.getDpkgVersion("bridge-utils")
	iprouteVersion = cmd.getDpkgVersion("iproute")
	tcpdumpVersion = cmd.getDpkgVersion("tcpdump")

	if bridgeUtilsVersion:
		connections.TYPES[Bridge.TYPE] = Bridge
	else:
		print "Warning: Bridge not supported on bridge-utils version %s" % bridgeUtilsVersion
	
	if iprouteVersion:
		Bridge.CAP_ATTRS.update(Bridge.CAP_ATTRS_EMUL)
		Bridge.CAP_ACTIONS.update(Bridge.CAP_ACTIONS_EMUL)
	else:
		print "Warning: Bridge link emulation needs iproute, disabled"
	
	if tcpdumpVersion:
		Bridge.CAP_ATTRS.update(Bridge.CAP_ATTRS_CAPTURE)
		Bridge.CAP_ACTIONS.update(Bridge.CAP_ACTIONS_CAPTURE)
	else:
		print "Warning: Bridge packet capturing needs tcpdump, disabled"