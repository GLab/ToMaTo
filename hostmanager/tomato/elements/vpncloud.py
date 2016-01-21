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

import os, shutil, hashlib, base64
from .. import connections, elements, config
from ..lib import util, cmd #@UnresolvedImport
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib.cmd import process, net, path #@UnresolvedImport
from ..lib.error import UserError, InternalError
from ..lib.newcmd import vpncloud

DOC="""
"""


ST_CREATED = "created"
ST_STARTED = "started"

class VpnCloud(elements.Element):
	port_attr = Attr("port", type="int")
	port = port_attr.attribute()
	pid_attr = Attr("pid", type="int", null=True)
	pid = pid_attr.attribute()
	network_id_attr = Attr("network_id", type="int")
	network_id = network_id_attr.attribute()
	peers_attr = Attr("peers", desc="Peers", states=[ST_CREATED], default=[])
	peers = peers_attr.attribute()

	TYPE = "vpncloud"
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
		"network_id": network_id_attr,
		"peers": peers_attr,
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [None]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DEFAULT_ATTRS = {}
	DOC = DOC
	__doc__ = DOC
	
	class Meta:
		db_table = "tomato_vpncloud"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.port = self.getResource("port")

	def _interfaceName(self):
		return "vpncloud%d" % self.id

	def interfaceName(self):
		return self._interfaceName() if self.state == ST_STARTED else None

	def modify_network_id(self, val):
		self.network_id = val

	def modify_peers(self, val):
		self.peers = val

	def action_start(self):
		UserError.check(self.network_id, UserError.INVALID_CONFIGURATION, "Network id must be set")
		self.pid = vpncloud.start(self._interfaceName(), config.PUBLIC_ADDRESS, self.port, self.network_id, self.peers)
		self.setState(ST_STARTED)
		net.ifUp(self._interfaceName())
		con = self.getConnection()
		if con:
			con.connectInterface(self._interfaceName())

	def action_stop(self):
		con = self.getConnection()
		if con:
			con.disconnectInterface(self._interfaceName())
		if self.pid:
			vpncloud.stop(self.pid)
		self.pid = None
		self.setState(ST_CREATED)

	def upcast(self):
		return self

	def updateUsage(self, usage, data):
		if self.pid:
			usage.memory = process.memory(self.pid)
			cputime = process.cputime(self.pid)
			usage.updateContinuous("cputime", cputime, data)
			trafficA, trafficB = net.trafficInfo(self.interfaceName())
			if not trafficA is None and not trafficB is None:
				traffic = trafficA + trafficB
				usage.updateContinuous("traffic", traffic, data)
			
if not config.MAINTENANCE:
	if vpncloud.isSupported():
		elements.TYPES[VpnCloud.TYPE] = VpnCloud
	else:
		print "Warning: VpnCloud not supported, disabled"