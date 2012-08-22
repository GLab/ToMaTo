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

from tomato import connections, host, fault
from tomato.lib.attributes import attribute, oneOf, between
from tomato.host import tc, net, process, path, fileserver

import os

DOC="""
	Description
	"""

class Bridge(connections.Connection):
	bridge = attribute("bridge", str)
	
	emulation = attribute("emulation", bool, default=False)
	ifb_num = attribute("ifb_num", int)
	bandwidth_to = attribute("bandwidth_to", between(0, 1000000, faultType=fault.new_user), default=0)
	bandwidth_from = attribute("bandwidth_from", between(0, 1000000, faultType=fault.new_user), default=0)
	lossratio_to = attribute("lossratio_to", between(0.0, 100.0, faultType=fault.new_user), default=0.0)
	lossratio_from = attribute("lossratio_from", between(0.0, 100.0, faultType=fault.new_user), default=0.0)
	duplicate_to = attribute("duplicate_to", between(0.0, 100.0, faultType=fault.new_user), default=0.0)
	duplicate_from = attribute("duplicate_from", between(0.0, 100.0, faultType=fault.new_user), default=0.0)
	corrupt_to = attribute("corrupt_to", between(0.0, 100.0, faultType=fault.new_user), default=0.0)
	corrupt_from = attribute("corrupt_from", between(0.0, 100.0, faultType=fault.new_user), default=0.0)
	delay_to = attribute("delay_to", between(0.0, 60000.0, faultType=fault.new_user), default=0.0)
	delay_from = attribute("delay_from", between(0.0, 60000.0, faultType=fault.new_user), default=0.0)
	jitter_to = attribute("jitter_to", between(0.0, 60000.0, faultType=fault.new_user), default=0.0)
	jitter_from = attribute("jitter_from", between(0.0, 60000.0, faultType=fault.new_user), default=0.0)
	distribution_to = attribute("distribution_to", str)
	distribution_from = attribute("distribution_from", str)
	
	capturing = attribute("capturing", bool, default=False)
	capture_filter = attribute("capture_filter", str, default="")
	capture_port = attribute("capture_port", int)
	capture_mode = attribute("capture_mode", oneOf(["net", "file"], faultType=fault.new_user), default="file")
	capture_pid = attribute("capture_pid", int)

	ST_CREATED = "created"
	ST_STARTED = "started"
	TYPE = "bridge"
	CAP_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		"__remove__": [ST_CREATED],
	}
	CAP_ACTIONS_EMUL = {
	}
	CAP_ACTIONS_CAPTURE = {
		"download_grant": [ST_CREATED, ST_STARTED],
	}
	CAP_ATTRS = {}
	CAP_ATTRS_EMUL = {
		"emulation": [ST_CREATED, ST_STARTED],
		"delay_to": [ST_CREATED, ST_STARTED],
		"delay_from": [ST_CREATED, ST_STARTED],
		"jitter_to": [ST_CREATED, ST_STARTED],
		"jitter_from": [ST_CREATED, ST_STARTED],
		"distribution_to": [ST_CREATED, ST_STARTED],
		"distribution_from": [ST_CREATED, ST_STARTED],
		"bandwidth_to": [ST_CREATED, ST_STARTED],
		"bandwidth_from": [ST_CREATED, ST_STARTED],
		"lossratio_to": [ST_CREATED, ST_STARTED],
		"lossratio_from": [ST_CREATED, ST_STARTED],
		"duplicate_to": [ST_CREATED, ST_STARTED],
		"duplicate_from": [ST_CREATED, ST_STARTED],
		"corrupt_to": [ST_CREATED, ST_STARTED],
		"corrupt_from": [ST_CREATED, ST_STARTED],
	}
	CAP_ATTRS_CAPTURE = {
		"capturing": [ST_CREATED, ST_STARTED],
		"capture_filter": [ST_CREATED, ST_STARTED],
		"capture_mode": [ST_CREATED, ST_STARTED],
	}
	DEFAULT_ATTRS = {"bandwidth_to": 10000, "bandwidth_from": 10000}
	CAP_CON_CONCEPTS = [(connections.CONCEPT_INTERFACE, connections.CONCEPT_INTERFACE)]
	DOC = DOC
	
	class Meta:
		db_table = "tomato_bridge"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		connections.Connection.init(self, *args, **kwargs) #no id and no attrs before this line
		self.bridge = "br%d" % self.id
		self.capture_port = self.getResource("port")
		self.ifb_num = self.getResource("ifb")
				
	def _startCapturing(self):
		if not self.capturing or self.state == self.ST_CREATED:
			return
		if self.capture_mode == "file":
			self.capture_pid = host.spawn(["tcpdump", "-i", self.bridge, "-n", "-C", "10", "-w", self.dataPath("capture"), "-U", "-W", "5", "-s0", self.capture_filter])
		elif self.capture_mode == "net":
			self.capture_pid = host.spawn(["tcpserver", "-qHRl", "0", "0", str(self.capture_port), "tcpdump", "-i", self.bridge, "-s0" "-nUw", "-", self.capture_filter])
		else:
			fault.raise_("Capture mode must be either file or net")
				
	def _stopCapturing(self):
		if not self.capturing or self.state == self.ST_CREATED:
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
		self._captureRestart |= self.capture_mode == val
		self.capture_mode = val
	
	def modify_capture_filter(self, val):
		self._captureRestart |= self.capture_filter == val
		self.capture_filter = val
	
	def _startEmulation(self):
		if not self.emulation:
			return
		els = self.getElements()
		if len(els) != 2:
			return
		ifA, ifB = [el.interfaceName() for el in els]
		if not ifA or not ifB:
			return
		if ifA.id > ifB.id:
			#force ordering on connected elements, so from and to have defined meanings
			ifA, ifB = ifB, ifA
		attrsA = dict([(k.replace("_from", ""), v) for k, v in self.attrs.iteritems() if k.endswith("_from")])
		attrsB = dict([(k.replace("_to", ""), v) for k, v in self.attrs.iteritems() if k.endswith("_to")])
		#FIXME: check if directions are correct
		tc.setLinkEmulation(ifA, **attrsA)
		tc.setLinkEmulation(ifB, **attrsB)
	
	def _stopEmulation(self):
		if not self.emulation:
			return
		els = self.getElements()
		if len(els) != 2:
			return
		ifA, ifB = [el.interfaceName() for el in els]
		if not ifA or not ifB:
			return
		tc.clearLinkEmulation(ifA)
		tc.clearLinkEmulation(ifB)
	
	def modify_emulation(self, val):
		if self.emulation == val:
			return
		self.emulation = val
		if self.emulation:
			self._startEmulation()
		if not self.emulation:
			self._stopEmulation()

	def modify_bandwith_to(self, val):
		self._emulRestart |= self.bandwidth_to != val
		self.bandwidth_to = val

	def modify_bandwith_from(self, val):
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
		self.setState(self.ST_STARTED)
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
		self.setState(self.ST_CREATED)

	def connectInterface(self, ifname):
		if self.state == self.ST_CREATED:
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
		if self.state == self.ST_CREATED:
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

	def action_download_grant(self):
		entries = [os.path.join(self.dataPath("capture"), f) for f in path.entries(self.dataPath("capture"))]
		fault.check(entries, "Nothing captured so far")
		host.run(["tcpslice", "-w", self.dataPath("capture.pcap")] + entries)
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
		usage.diskspace = host.path.diskspace(self.dataPath())

bridgeUtilsVersion = host.getDpkgVersion("bridge-utils")
iprouteVersion = host.getDpkgVersion("iproute")
tcpdumpVersion = host.getDpkgVersion("tcpdump")

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