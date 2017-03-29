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
from ..lib.constants import ActionName,StateName
from ..db import *
from ..generic import *
import os

DOC="""
	Description
	"""

class Bridge(connections.Connection):

	bridge = StringField()

	emulation = BooleanField(default=True)

	bandwidth_to = FloatField(default=10000, min_value=0, max_value=1000000)
	bandwidth_from = FloatField(default=10000, min_value=0, max_value=1000000)
	lossratio_to = FloatField(default=0.0, min_value=0, max_value=100)
	lossratio_from =FloatField(default=0.0, min_value=0, max_value=100)
	duplicate_to = FloatField(default=0.0, min_value=0, max_value=100)
	duplicate_from = FloatField(default=0.0, min_value=0, max_value=100)
	corrupt_to = FloatField(default=0.0, min_value=0, max_value=100)
	corrupt_from = FloatField(default=0.0, min_value=0, max_value=100)
	delay_to = FloatField(default=0.0, min_value=0)
	delay_from = FloatField(default=0.0, min_value=0)
	jitter_to = FloatField(default=0.0, min_value=0)
	jitter_from = FloatField(default=0.0, min_value=0)
	distribution_to = StringField(choices = ["uniform", "normal", "pareto", "paretonormal"], default="uniform")
	distribution_from = StringField(choices = ["uniform", "normal", "pareto", "paretonormal"], default="uniform")

	capturing = BooleanField(default=False)
	capture_filter = StringField(default="")
	capture_port = IntField()
	capture_mode = StringField(choices=["net", "file"], default="file")
	capture_pid = IntField()





	TYPE = "bridge"
	DEFAULT_ATTRS = {"bandwidth_to": 10000, "bandwidth_from": 10000}
	CAP_CON_CONCEPTS = [(connections.CONCEPT_INTERFACE, connections.CONCEPT_INTERFACE)]
	DOC = DOC
	__doc__ = DOC #@ReservedAssignment

	@property
	def type(self):
		return self.TYPE

	def init(self, *args, **kwargs):
		self.state = StateName.CREATED
		connections.Connection.init(self, *args, **kwargs) #no id and no attrs before this line
		self.bridge = "br%s" % str(self.id)[13:24]
		self.capture_port = self.getResource("port")
				
	def _startCapturing(self):
		if not self.capturing or self.state == StateName.CREATED:
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
		if not self.capturing or self.state == StateName.CREATED:
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
		attrsA = dict([(k.replace("_to", ""), v) for k, v in self.info().iteritems() if k.endswith("_to")])
		attrsB = dict([(k.replace("_from", ""), v) for k, v in self.info().iteritems() if k.endswith("_from")])
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

	def modify(self, **attrs):
		self._emulRestart = False
		self._captureRestart = False
		connections.Connection.modify(self, **attrs)
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
		self.setState(StateName.STARTED)
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
		self.setState(StateName.CREATED)

	def remove(self):
		self.action_stop()
		connections.Connection.remove(self)

	def connectInterface(self, ifname):
		if self.state == StateName.CREATED:
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
		if self.state == StateName.CREATED:
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

	ATTRIBUTES = connections.Connection.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"bridge": Attribute(field=bridge, schema=schema.String(), readOnly=True),
	})
	ATTRIBUTES_EMUL = {
		"emulation": Attribute(field=emulation, description="Enable emulation", schema=schema.Bool(), default=True),

		"bandwidth_to": Attribute(field=bandwidth_to, description="Bandwidth in kbit/s",
								 schema=schema.Number(minValue=0, maxValue=1000000), set=modify_bandwidth_to,
								 default=10000),
		"bandwidth_from": Attribute(field=bandwidth_from, description="Bandwidth in kbit/s",
								   schema=schema.Number(minValue=0, maxValue=1000000), set=modify_bandwidth_from,
								   default=10000),

		"lossratio_to": Attribute(field=lossratio_to, description="Loss ratio in kbit/s",
								  schema=schema.Number(minValue=0, maxValue=1000000), set=modify_lossratio_to,
								  default=10000),
		"lossratio_from": Attribute(field=lossratio_from, description="Loss ratio in kbit/s",
									schema=schema.Number(minValue=0, maxValue=1000000), set=modify_lossratio_from,
									default=10000),

		"duplicate_to": Attribute(field=duplicate_to, description="Duplication ratio in %",
								  schema=schema.Number(minValue=0.0, maxValue=100.0), set=modify_duplicate_to,
								  default=0.0),
		"duplicate_from": Attribute(field=duplicate_from, description="Duplication ratio in %",
									schema=schema.Number(minValue=0.0, maxValue=100.0), set=modify_duplicate_from,
									default=0.0),

		"corrupt_to": Attribute(field=corrupt_to, description="Corruption ratio in %",
								schema=schema.Number(minValue=0.0, maxValue=100.0), set=modify_corrupt_to, default=0.0),
		"corrupt_from": Attribute(field=corrupt_from, description="Corruption ratio in %",
								  schema=schema.Number(minValue=0.0, maxValue=100.0), set=modify_corrupt_from,
								  default=0.0),

		"delay_to": Attribute(field=delay_to, description="Delay in ms",
							  schema=schema.Number(minValue=0.0), set=modify_delay_to, default=0.0),
		"delay_from": Attribute(field=delay_from, description="Delay in ms",
								schema=schema.Number(minValue=0.0), set=modify_delay_from, default=0.0),

		"jitter_to": Attribute(field=jitter_to, description="Jitter in ms",
							   schema=schema.Number(minValue=0.0), set=modify_jitter_to, default=0.0),
		"jitter_from": Attribute(field=jitter_from, description="Jitter in ms",
								 schema=schema.Number(minValue=0.0), set=modify_jitter_from, default=0.0),

		"distribution_to": Attribute(field=distribution_to, description="Distribution",
									 schema=schema.String(options=["uniform", "normal", "pareto", "paretonormal"]),
									 set=modify_distribution_to,
									 default="uniform"),
		"distribution_from": Attribute(field=distribution_from, description="Distribution",
									   schema=schema.String(options=["uniform", "normal", "pareto", "paretonormal"]),
									   set=modify_distribution_from,
									   default="uniform"),
	}

	ATTRIBUTES_CAPTURE = {
		"capturing": Attribute(field=capturing, description="Enable packet capturing", schema=schema.Bool(),
							   set=modify_capturing,
							   default=False),
		"capture_filter": Attribute(field=capture_filter, description="Packet filter expression",
									schema=schema.String(), set=modify_capture_filter, default=""),
		"capture_port": Attribute(field=capture_port, schema=schema.Int(), readOnly=True),
		"capture_pid": Attribute(field=capture_pid, schema=schema.Int(), readOnly=True),
		"capture_mode": Attribute(field=capture_mode, description="Capture mode", set=modify_capture_mode,
								  schema=schema.String(options=["net", "file"]), default="file"),

	}

	ACTIONS = connections.Connection.ACTIONS.copy()
	ACTIONS.update({ActionName.START: StatefulAction(action_start, allowedStates=[StateName.CREATED],
										 stateChange=StateName.STARTED),
					ActionName.STOP: StatefulAction(action_stop, allowedStates=[StateName.STARTED],
										stateChange=StateName.CREATED),

	})
	ACTIONS_EMUL = {}
	ACTIONS_CAPTURE = {
		ActionName.DOWNLOAD_GRANT: StatefulAction(action_download_grant,
												  allowedStates=[StateName.CREATED, StateName.STARTED]),
	}

if not config.MAINTENANCE:
	bridgeUtilsVersion = cmd.getDpkgVersion("bridge-utils")
	iprouteVersion = cmd.getDpkgVersion("iproute")
	tcpdumpVersion = cmd.getDpkgVersion("tcpdump")

	if bridgeUtilsVersion:
		connections.TYPES[Bridge.TYPE] = Bridge
	else:
		print "Warning: Bridge not supported on bridge-utils version %s" % bridgeUtilsVersion
	
	if iprouteVersion:
		Bridge.ATTRIBUTES.update(Bridge.ATTRIBUTES_EMUL)
		Bridge.ACTIONS.update(Bridge.ACTIONS_EMUL)
	else:
		print "Warning: Bridge link emulation needs iproute, disabled"
	
	if tcpdumpVersion:
		Bridge.ATTRIBUTES.update(Bridge.ATTRIBUTES_CAPTURE)
		Bridge.ACTIONS.update(Bridge.ACTIONS_CAPTURE)
	else:
		print "Warning: Bridge packet capturing needs tcpdump, disabled"