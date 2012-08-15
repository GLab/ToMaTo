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

import os
from django.db import models
from tomato import connections, host
from tomato.lib.attributes import attribute

DOC="""
	Description
	"""

class Bridge(connections.Connection):
	bridge = attribute("bridge", str)

	ST_CREATED = "created"
	ST_STARTED = "started"
	TYPE = "bridge"
	CAP_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		"__remove__": [ST_CREATED],
	}
	CAP_ATTRS = {}
	DEFAULT_ATTRS = {}
	CAP_CON_PARADIGMS = [(connections.PARADIGM_INTERFACE, connections.PARADIGM_INTERFACE)]
	
	class Meta:
		db_table = "tomato_bridge"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		connections.Connection.init(self, *args, **kwargs) #no id and no attrs before this line
		self.bridge = "br%d" % self.id
				
	def _bridgeObj(self):
		return host.Bridge(self.bridge)
				
	def action_start(self):
		br = self._bridgeObj()
		br.create()
		br.up()
		self.setState(self.ST_STARTED)
		for el in self.getElements():
			ifname = el.interfaceName()
			if ifname:
				self.connectInterface(ifname)
				
	def action_stop(self):
		br = self._bridgeObj()
		for el in self.getElements():
			ifname = el.interfaceName()
			if ifname:
				self.disconnectInterface(ifname)
		if br.exists():
			br.down()
			br.remove()
		self.setState(self.ST_CREATED)

	def connectInterface(self, ifname):
		br = self._bridgeObj()
		if ifname in br.interfaceNames():
			return
		iface = host.Interface(ifname)
		if iface.getBridge():
			iface.getBridge().removeInterface(iface)
		br.addInterface(iface)
		if len(br.interfaces()) == 2:
			# now elements are connected
			for el in self.getElements():
				el.onConnected()
	
	def disconnectInterface(self, ifname):
		br = self._bridgeObj()
		if not br.exists():
			return
		if not ifname in br.interfaceNames():
			return
		if len(br.interfaces()) == 2:
			# now elements are no longer connected
			for el in self.getElements():
				el.onDisconnected()
		br.removeInterface(host.Interface(ifname))

	def upcast(self):
		return self

	def info(self):
		info = connections.Connection.info(self)
		return info


bridgeUtilsVersion = host.getDpkgVersion("bridge-utils")

if bridgeUtilsVersion:
	connections.TYPES[Bridge.TYPE] = Bridge
else:
	print "Warning: Bridge not supported on bridge-utils version %s" % bridgeUtilsVersion