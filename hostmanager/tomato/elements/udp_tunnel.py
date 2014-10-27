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

from .. import connections, elements, config
from ..lib import util, cmd #@UnresolvedImport
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib.cmd import net, process #@UnresolvedImport
from ..lib.error import InternalError

DOC="""
Element type: ``udp_tunnel``

Description:
	This element type represents one endpoint of a UDP tunnel. Ethernet 
	packages are encapsulated in UDP packets and senf/received via this
	endpoint.
	The tunnel needs exactly one corresponding endpoint that it sends the
	packets to/receives packets from. For the tunnel to work, at least one of
	the endpoints must have a connect attribute set to the address and port of
	the remote endpoint.

Possible parents: None

Possible children: None

Default state: *created*

Removable in states: *created*

Connection concepts: *interface*

States:
	*created*: In this state, the endpoint is known but not active.
	*started*: In this state, the endpoint is active and ready to send/receive packets. 
		
Attributes:
	*connect*: str, changeable in state *created*, default: ``None``
		If this attribute is set to a value this endpoint is in conect mode,
		i.e. it will connect to the endpoint given by the connect attribute in
		the form host:port.
		Note: For the tunnel to work, at least one of the endpoints must have a
		connect attribute set to the address and port of the remote endpoint.
	*port*: int, read-only
		The port on this host on which the endpoint is listening in state 
		started.
		
Actions:
	*start*, callable in state *created*, next state: *started*
	 	Starts the endpoint so that it is ready to send/receive packets.
	*stop*, callable in state *started*, next state: *created*
	 	Stops the endpoint.
"""

ST_CREATED = "created"
ST_STARTED = "started"

class UDP_Tunnel(elements.Element):
	pid_attr = Attr("pid", type="int")
	pid = pid_attr.attribute()
	port_attr = Attr("port", type="int")
	port = port_attr.attribute()
	connect_attr = Attr("connect", desc="Connect to", states=[ST_CREATED], type="str", null=True, default=None)
	connect = connect_attr.attribute()

	TYPE = "udp_tunnel"
	CAP_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CAP_NEXT_STATE = {
		"start": ST_STARTED,
		"stop": ST_CREATED,
	}		
	CAP_ATTRS = {
		"connect": connect_attr,
		"timeout": elements.Element.timeout_attr
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [None]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DEFAULT_ATTRS = {}
	DOC = DOC
	__doc__ = DOC
	
	class Meta:
		db_table = "tomato_udp_tunnel"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.port = self.getResource("port")

	def _getState(self):
		return ST_STARTED if self.pid and process.exists(self.pid) else ST_CREATED

	def _checkState(self):
		savedState = self.state
		realState = self._getState()
		if savedState != realState:
			self.setState(realState, True)
		InternalError.check(savedState == realState, InternalError.WRONG_DATA, "Saved state is wrong",
			data={"type": self.type, "id": self.id, "saved_state": savedState, "real_state": realState})

	def _interfaceName(self):
		return "stap%d" % self.id

	def interfaceName(self):
		return self._interfaceName() if self.state == ST_STARTED else None
				
	def modify_connect(self, val):
		self.connect = val

	def action_start(self):
		cmd_ = ["socat", "tun:127.0.0.1/32,tun-type=tap,iff-up,tun-name=%s" % self._interfaceName()]
		if self.connect:
			cmd_.append("udp-connect:%s,sourceport=%d" % (self.connect, self.port))
		else:
			cmd_.append("udp-listen:%d" % self.port)
		self.pid = cmd.spawn(cmd_)
		self.setState(ST_STARTED)
		ifName = self._interfaceName()
		InternalError.check(util.waitFor(lambda :net.ifaceExists(ifName)), InternalError.ASSERTION,
			"Interface did not start properly", data={"interface": ifName})
		con = self.getConnection()
		if con:
			con.connectInterface(self._interfaceName())

	def action_stop(self):
		con = self.getConnection()
		if con:
			con.disconnectInterface(self._interfaceName())
		if self.pid:
			process.kill(self.pid)
			del self.pid
		self.setState(ST_CREATED)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		return info

	def updateUsage(self, usage, data):
		self._checkState()
		if self.state == ST_CREATED:
			return
		usage.memory = process.memory(self.pid)
		cputime = process.cputime(self.pid)
		usage.updateContinuous("cputime", cputime, data)
		try:
			traffic = sum(net.trafficInfo(self.interfaceName()))
		except: #Tunnel just quit
			traffic = 0
		usage.updateContinuous("traffic", traffic, data)

if not config.MAINTENANCE:
	socatVersion = cmd.getDpkgVersion("socat")
	if socatVersion:
		elements.TYPES[UDP_Tunnel.TYPE] = UDP_Tunnel
	else:
		print "Warning: UDP_Tunnel needs socat, disabled"