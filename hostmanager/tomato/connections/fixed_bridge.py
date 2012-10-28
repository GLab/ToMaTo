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
from ..lib.cmd import net #@UnresolvedImport

DOC="""
	Description
	"""

#TODO: implement capturing
#TODO: implement link emulation using ifbs

ST_DEFAULT = "default"

class Fixed_Bridge(connections.Connection):
	TYPE = "fixed_bridge"
	CAP_ACTIONS = {
		connections.REMOVE_ACTION: [ST_DEFAULT],
	}
	CAP_ATTRS = {}
	DEFAULT_ATTRS = {}
	CAP_CON_CONCEPTS = [(connections.CONCEPT_BRIDGE, connections.CONCEPT_INTERFACE)]
	DOC = DOC
	__doc__ = DOC
	
	class Meta:
		db_table = "tomato_fixed_bridge"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_DEFAULT
		connections.Connection.init(self, *args, **kwargs) #no id and no attrs before this line
		
	def _bridgeName(self):
		for el in self.getElements():
			if connections.CONCEPT_BRIDGE in el.CAP_CON_CONCEPTS:
				name = el.bridgeName()
				if name:
					return name
		return None

	def _ifaceName(self):
		for el in self.getElements():
			if connections.CONCEPT_INTERFACE in el.CAP_CON_CONCEPTS:
				name = el.interfaceName()
				if name:
					return name
		return None

	def _connect(self, ifname, brname):
		oldBridge = net.interfaceBridge(ifname)
		if oldBridge:
			net.bridgeRemoveInterface(oldBridge, ifname)
		net.bridgeAddInterface(brname, ifname)
		# now elements are connected
		for el in self.getElements():
			el.onConnected()

	def connectInterface(self, ifname):
		brname = self._bridgeName()
		if not brname:
			return
		self._connect(ifname, brname)
		
	
	def disconnectInterface(self, ifname):
		oldBridge = net.interfaceBridge(ifname)
		if oldBridge:
			net.bridgeRemoveInterface(oldBridge, ifname)
		# now elements are connected
		for el in self.getElements():
			el.onConnected()

	def connectBridge(self, brname):
		ifname = self._ifaceName()
		if not ifname:
			return
		self._connect(ifname, brname)
	
	def disconnectBridge(self, brname):
		ifname = self._ifaceName()
		if not ifname:
			return
		net.bridgeRemoveInterface(brname, ifname)
		# now elements are connected
		for el in self.getElements():
			el.onConnected()

	def remove(self):
		self.checkRemove()
		ifname = self._ifaceName()
		brname = self._bridgeName()
		if ifname and brname:
			net.bridgeRemoveInterface(brname, ifname)
		connections.Connection.remove(self)

	def upcast(self):
		return self

	def info(self):
		info = connections.Connection.info(self)
		return info

	def updateUsage(self, usage, data):
		ifname = self._ifaceName()
		if ifname and net.ifaceExists(ifname):
			traffic = sum(net.trafficInfo(ifname))
			usage.updateContinuous("traffic", traffic, data)


if not config.MAINTENANCE:
	bridgeUtilsVersion = cmd.getDpkgVersion("bridge-utils")

	if bridgeUtilsVersion:
		connections.TYPES[Fixed_Bridge.TYPE] = Fixed_Bridge
	else:
		print "Warning: fixed_bridge not supported on bridge-utils version %s" % bridgeUtilsVersion