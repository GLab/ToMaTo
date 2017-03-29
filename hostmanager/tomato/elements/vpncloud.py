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
from ..db import *
from ..generic import *
from .. import connections, elements, config
from ..lib import util, cmd #@UnresolvedImport
from ..lib.attributes import Attr #@UnresolvedImport
from ..lib.cmd import process, net, path #@UnresolvedImport
from ..lib.error import UserError, InternalError
from ..lib.newcmd import vpncloud
from ..lib.constants import ActionName, StateName, TypeName

DOC="""
"""

class VpnCloud(elements.Element):
	port = IntField()
	pid = IntField(null=True)
	network_id = IntField()
	peers = ListField(default=[])

	ATTRIBUTES = elements.Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"port": Attribute(field=port, schema=schema.Int(), readOnly=True),
		"pid": Attribute(field=pid, schema=schema.Int(null=True), readOnly=True),
		"network_id": Attribute(field=network_id,  description="Network ID", schema=schema.Int()),
		"peers": Attribute(field=peers, label="Peers", schema=schema.List(), default=[])
	})



	TYPE = TypeName.VPNCLOUD

	CAP_CHILDREN = {}
	CAP_PARENT = [None]
	CAP_CON_CONCEPTS = [connections.CONCEPT_INTERFACE]
	DEFAULT_ATTRS = {}
	DOC = DOC
	__doc__ = DOC

	@property
	def type(self):
		return self.TYPE

	def init(self, *args, **kwargs):
		self.state = StateName.CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		self.port = self.getResource("port")

	def _interfaceName(self):
		return TypeName.VPNCLOUD + "%s" % str(self.id)[16:24]

	def interfaceName(self):
		return self._interfaceName() if self.state == StateName.STARTED else None

	def modify_network_id(self, val):
		self.network_id = val

	def modify_peers(self, val):
		self.peers = val

	def action_start(self):
		UserError.check(self.network_id, UserError.INVALID_CONFIGURATION, "Network id must be set")
		self.pid = vpncloud.start(self._interfaceName(), config.PUBLIC_ADDRESS, self.port, self.network_id, self.peers)
		self.setState(StateName.STARTED)
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
		self.setState(StateName.CREATED)

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


	ACTIONS = elements.Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(elements.Element.remove, check=elements.Element.checkRemove,
											 allowedStates=[StateName.CREATED]),
		ActionName.START: StatefulAction(action_start, allowedStates=[StateName.CREATED],
										 stateChange=StateName.STARTED),
		ActionName.STOP: StatefulAction(action_stop, allowedStates=[StateName.STARTED],
										stateChange=StateName.CREATED),
	})

if not config.MAINTENANCE:
	if vpncloud.isSupported():
		elements.TYPES[VpnCloud.TYPE] = VpnCloud
	else:
		print "Warning: VpnCloud not supported, disabled"