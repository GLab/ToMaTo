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

import os, sys, json
from django.db import models
from tomato import connections, elements, resources, config, host, fault
from tomato.resources import network
from tomato.lib.attributes import attribute
from tomato.lib import decorators, util

DOC="""
Element type: external_network

Description:
	This element type provides access to external networks present at this 
	host as a bridge.

Possible parents: None

Possible children: None

Default state: default

Removable in states: default

Connection paradigms: bridge

States:
	default: This is the only possible state. In this state the bridge is 
		present and ready.
		
Attributes:
	network: str, changeable in all states
		The kind of network to be chosen for this external network. A network
		resource with a matching kind attribute is chosen as network for this
		element. If no network with the given kind exists (esp. for 
		network=None), a default network is chosen instead.

Actions: None
"""


class External_Network(elements.Element):
	network = models.ForeignKey(network.Network, null=True)

	ST_DEFAULT = "default"
	TYPE = "external_network"
	CAP_ACTIONS = {
		"__remove__": [ST_DEFAULT],
	}
	CAP_ATTRS = {
		"network": [ST_DEFAULT],
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [None]
	CAP_CON_PARADIGMS = [connections.PARADIGM_BRIDGE]
	DEFAULT_ATTRS = {}
	
	class Meta:
		db_table = "tomato_external_network"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_DEFAULT
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		#network: None, default network
				
	def modify_network(self, kind):
		con = self.getConnection()
		br = self.bridgeName()
		if con and br:
			con.disconnectBridge(br)
		self.network = resources.network.get(kind)
		br = self.bridgeName()
		if con and br:
			con.connectBridge(br)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["network"] = self.network.kind if self.network else None
		return info

	def bridgeName(self):
		return self.network.getBridge() if self.network else None

elements.TYPES[External_Network.TYPE] = External_Network
