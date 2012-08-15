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

class Fixed_Bridge(connections.Connection):
	ST_DEFAULT = "default"
	TYPE = "fixed_bridge"
	CAP_ACTIONS = {
		"__remove__": [ST_DEFAULT],
	}
	CAP_ATTRS = {}
	DEFAULT_ATTRS = {}
	CAP_CON_PARADIGMS = [(connections.PARADIGM_BRIDGE, connections.PARADIGM_INTERFACE)]
	
	class Meta:
		db_table = "tomato_fixed_bridge"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_DEFAULT
		connections.Connection.init(self, *args, **kwargs) #no id and no attrs before this line
		
	def _bridgeObj(self):
		for el in self.getElements():
			if connections.PARADIGM_BRIDGE in el.CAP_CON_PARADIGMS:
				name = el.bridgeName()
				if name:
					return host.Bridge(name)
		return None

	def _ifaceObj(self):
		for el in self.getElements():
			if connections.PARADIGM_INTERFACE in el.CAP_CON_PARADIGMS:
				name = el.interfaceName()
				if name:
					return host.Interface(name)
		return None

	def _connect(self, iface, br):
		if iface.getBridge():
			iface.getBridge().removeInterface(iface)
		br.addInterface(iface)
		# now elements are connected
		for el in self.getElements():
			el.onConnected()

	def connectInterface(self, ifname):
		iface = host.Interface(ifname)
		br = self._bridgeObj()
		if not br:
			return
		self._connect(iface, br)
		
	
	def disconnectInterface(self, ifname):
		iface = host.Interface(ifname)
		if iface.getBridge():
			iface.getBridge().removeInterface(iface)
		# now elements are connected
		for el in self.getElements():
			el.onConnected()

	def connectBridge(self, brname):
		iface = self._ifaceObj()
		if not iface:
			return
		br = host.Bridge(brname)
		self._connect(iface, br)
	
	def disconnectBridge(self, brname):
		iface = self._ifaceObj()
		if not iface:
			return
		br = host.Bridge(brname)
		br.removeInterface(iface)
		# now elements are connected
		for el in self.getElements():
			el.onConnected()

	def remove(self):
		self.checkRemove()
		iface = self._ifaceObj()
		br = self._bridgeObj()
		if iface and br:
			br.removeInterface(iface)
		connections.Connection.remove(self)

	def upcast(self):
		return self

	def info(self):
		info = connections.Connection.info(self)
		return info


bridgeUtilsVersion = host.getDpkgVersion("bridge-utils")

if bridgeUtilsVersion:
	connections.TYPES[Fixed_Bridge.TYPE] = Fixed_Bridge
else:
	print "Warning: fixed_bridge not supported on bridge-utils version %s" % bridgeUtilsVersion