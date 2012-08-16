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

from tomato import connections, elements, host
from tomato.lib import util
from tomato.lib.attributes import attribute

DOC="""
Element type: udp_tunnel

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

Default state: created

Removable in states: created

Connection paradigms: interface

States:
	created: In this state, the endpoint is known but not active.
	started: In this state, the endpoint is active and ready to 
		send/receive packets. 
		
Attributes:
	connect: str, changeable in state created, default: None
		If this attribute is set to a value this endpoint is in conect mode,
		i.e. it will connect to the endpoint given by the connect attribute in
		the form host:port.
		Note: For the tunnel to work, at least one of the endpoints must have a
		connect attribute set to the address and port of the remote endpoint.
	port: int, read-only
		The port on this host on which the endpoint is listening in state 
		started.
		
Actions:
	start, callable in state created
	 	Starts the endpoint so that it is ready to send/receive packets.
	stop, callable in state started
	 	Stops the endpoint.
"""


class UDP_Tunnel(elements.Element):
	pid = attribute("pid", int)
	port = attribute("port", int)
	connect = attribute("connect", str)

	ST_CREATED = "created"
	ST_STARTED = "started"
	TYPE = "udp_tunnel"
	CAP_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		"__remove__": [ST_CREATED],
	}
	CAP_ATTRS = {
		"connect": [ST_CREATED],
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [None]
	CAP_CON_PARADIGMS = [connections.PARADIGM_INTERFACE]
	DEFAULT_ATTRS = {}
	
	class Meta:
		db_table = "tomato_udp_tunnel"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.port = self.getResource("port")

	def _interfaceName(self):
		return "stap%d" % self.id

	def interfaceName(self):
		return self._interfaceName() if self.state == self.ST_STARTED else None
				
	def modify_connect(self, val):
		self.connect = val

	def action_start(self):
		cmd = ["socat", "tun:127.0.0.1/32,tun-type=tap,iff-up,tun-name=%s" % self._interfaceName()]
		if self.connect:
			cmd.append("udp-connect:%s,fork,sourceport=%d" % (host.escape(self.connect), self.port))
		else:
			cmd.append("udp-listen:%d,fork" % self.port)
		self.pid = host.spawn(cmd)
		self.setState(self.ST_STARTED)
		ifObj = host.Interface(self._interfaceName())
		util.waitFor(ifObj.exists)
		con = self.getConnection()
		if con:
			con.connectInterface(self._interfaceName())

	def action_stop(self):
		con = self.getConnection()
		if con:
			con.disconnectInterface(self._interfaceName())
		if self.pid:
			host.kill(self.pid)
			del self.pid
		self.setState(self.ST_CREATED)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		return info

socatVersion = host.getDpkgVersion("socat")

if socatVersion:
	elements.TYPES[UDP_Tunnel.TYPE] = UDP_Tunnel
else:
	print "Warning: UDP_Tunnel needs socat, disabled"