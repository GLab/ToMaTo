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

class Bridge(connections.Connection):
	bridge = attribute("bridge", str)

	ST_CREATED = "created"
	ST_PREPARED = "prepared"
	ST_STARTED = "started"
	TYPE = "bridge"
	CAP_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
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
				
	def action_prepare(self):
		#FIXME: implement
		self.setState(self.ST_PREPARED)
		
	def action_destroy(self):
		#FIXME: implement
		self.setState(self.ST_CREATED)

	def action_start(self):
		#FIXME: implement
		self.setState(self.ST_STARTED)
				
	def action_stop(self):
		#FIXME: implement
		self.setState(self.ST_PREPARED)

	def connectInterface(self, ifname):
		pass
	
	def disconectInterface(self, ifname):
		pass

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