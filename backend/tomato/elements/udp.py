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
from .. import elements, host, fault
from ..lib.attributes import Attr #@UnresolvedImport
from generic import ST_CREATED, ST_PREPARED, ST_STARTED

class UDP_Endpoint(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	name_attr = Attr("name", desc="Name", type="str")
	name = name_attr.attribute()
	connect_attr = Attr("connect", desc="Connect to", type="str", default="", states=[ST_CREATED, ST_PREPARED])
	connect = connect_attr.attribute()
	
	CUSTOM_ACTIONS = {
		"stop": [ST_STARTED],
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"name": name_attr,
		"connect": connect_attr,
	}
	DIRECT_ATTRS_EXCLUDE = ["timeout"]
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}

	TYPE = "udp_endpoint"
	HOST_TYPE = "udp_tunnel"
	CAP_CHILDREN = {}
	CAP_CONNECTABLE = True
	
	class Meta:
		db_table = "tomato_udp_endpoint"
		app_label = 'tomato'
			
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	def remoteType(self):
		return "udp_tunnel"
	
	def mainElement(self):
		return self.element
	
	def modify_name(self, val):
		self.name = val

	def modify_connect(self, val):
		self.connect = val
		if self.element:
			self.element.modify({"connect": val})

	def onError(self, exc):
		if self.element:
			try:
				self.element.updateInfo()
			except fault.XMLRPCError, exc:
				if exc.faultCode == fault.UNKNOWN_OBJECT:
					self.element.state = ST_CREATED
			self.setState(self.element.state, True)
			if self.state == ST_CREATED:
				if self.element:
					self.element.remove()
				for iface in self.getChildren():
					iface._remove()
				self.element = None
			self.save()

	def action_prepare(self):
		_host = host.select(elementTypes=[self.remoteType()])
		fault.check(_host, "No matching host found for element %s", self.TYPE)
		attrs = self._remoteAttrs()
		attrs.update({
			"connect": self.connect,
		})
		self.element = _host.createElement(self.remoteType(), parent=None, attrs=attrs, owner=self)
		self.save()
		self.setState(ST_PREPARED, True)
		
	def action_destroy(self):
		if self.element:
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	def action_stop(self):
		if self.element:
			self.element.action("stop")
		self.setState(ST_PREPARED, True)

	def upcast(self):
		return self

	def after_start(self):
		self.triggerConnectionStart()
		
	def after_stop(self):
		self.triggerConnectionStop()

	def readyToConnect(self):
		return self.state == ST_STARTED

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["connect"] = self.connect
		return info
	
elements.TYPES[UDP_Endpoint.TYPE] = UDP_Endpoint