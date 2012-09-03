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

from django.db import models
from tomato import elements, host, fault
from tomato.lib.attributes import attribute, oneOf #@UnresolvedImport
from generic import ST_CREATED, ST_PREPARED, ST_STARTED

class Tinc_VPN(elements.Element):
	name = attribute("name", str)
	mode = attribute("mode", oneOf(["switch", "hub"]), default="switch")
	
	CUSTOM_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"name": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"mode": [ST_CREATED, ST_PREPARED],
	}

	DIRECT_ATTRS_EXCLUDE = []
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}

	TYPE = "tinc_vpn"
	DIRECT_ATTRS_EXCLUDE = []
	CAP_CHILDREN = {"tinc_endpoint": [ST_CREATED, ST_PREPARED]}
	
	class Meta:
		db_table = "tomato_tinc_vpn"
		app_label = 'tomato'

	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	def mainElement(self):
		return None
	
	def onChildAdded(self, iface):
		if self.state == ST_PREPARED:
			iface.action("create", {})
			self._crossConnect()

	def onChildRemoved(self, iface):
		if self.state == ST_PREPARED:
			iface.action("destroy", {})
			self._crossConnect()

	def modify_name(self, val):
		self.name = val

	def modify_mode(self, val):
		self.mode = val
		for ch in self.getChildren():
			ch.modify({"mode": self.mode})

	def _crossConnect(self):
		assert self.state == ST_PREPARED
		peers = []
		for ch in self.getChildren():
			assert ch.element
			info = ch.info()
			print info
			peers.append({
				"host": ch.element.host.address,
				"port": info["attrs"]["port"],
				"pubkey": info["attrs"]["pubkey"],
			})
		for ch in self.getChildren():
			info = ch.info()
			others = filter(lambda p: p["pubkey"] != info["attrs"]["pubkey"], peers)
			ch.modify({"peers": others})

	def action_prepare(self):
		for ch in self.getChildren():
			if ch.state == ST_CREATED:
				ch.action("prepare", {})
		self.setState(ST_PREPARED)
		self._crossConnect()
		
	def action_destroy(self):
		for ch in self.getChildren():
			if ch.state == ST_PREPARED:
				ch.action("destroy", {})
		self.setState(ST_CREATED)

	def action_stop(self):
		for ch in self.getChildren():
			if ch.state == ST_STARTED:
				ch.action("stop", {})
		self.setState(ST_PREPARED)

	def action_start(self):
		for ch in self.getChildren():
			if ch.state == ST_STARTED:
				ch.action("start", {})
		self.setState(ST_STARTED)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["mode"] = self.mode
		return info



class Tinc_Endpoint(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	name = attribute("name", str)
	mode = attribute("mode", oneOf(["switch", "hub"]), default="switch")
	peers = attribute("peers", list, default=[])
	
	CUSTOM_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"name": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"mode": [ST_CREATED, ST_PREPARED],
		"peers": [ST_CREATED, ST_PREPARED],
	}
	DIRECT_ATTRS_EXCLUDE = []
	CAP_PARENT = [None, Tinc_VPN.TYPE]
	DEFAULT_ATTRS = {}

	TYPE = "tinc_endpoint"
	DIRECT_ATTRS_EXCLUDE = []
	CAP_CHILDREN = {}
	
	class Meta:
		db_table = "tomato_tinc_endpoint"
		app_label = 'tomato'
			
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	def remoteType(self):
		return "tinc"
	
	def mainElement(self):
		return self.element
	
	def modify_name(self, val):
		self.name = val

	def modify_mode(self, val):
		self.mode = val
		if self.element:
			self.element.modify({"mode": val})

	def modify_peers(self, val):
		self.peers = val
		if self.element:
			self.element.modify({"peers": val})

	def onError(self, exc):
		if self.element:
			self.element.updateInfo()
			self.setState(self.element.state, True)
			if self.state == ST_CREATED:
				if self.element:
					self.element.remove()
				for iface in self.getChildren():
					iface._remove()
				self.element = None
			self.save()

	def action_prepare(self):
		_host = host.select(elementTypes=["tinc"])
		fault.check(_host, "No matching host found for element %s", self.TYPE)
		attrs = self._remoteAttrs()
		attrs.update({
			"mode": self.mode,
			"peers": self.peers,
		})
		self.element = _host.createElement(self.remoteType(), parent=None, attrs=attrs)
		self.save()
		self.setState(ST_PREPARED, True)
		
	def action_destroy(self):
		if self.element:
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["mode"] = self.mode
		info["attrs"]["peers"] = self.peers
		return info
	
elements.TYPES[Tinc_VPN.TYPE] = Tinc_VPN	
elements.TYPES[Tinc_Endpoint.TYPE] = Tinc_Endpoint