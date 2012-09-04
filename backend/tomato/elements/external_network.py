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
from tomato.lib.attributes import attribute #@UnresolvedImport

ST_CREATED = "created"
ST_STARTED = "started"

class External_Network(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	site = models.ForeignKey(host.Site, null=True, on_delete=models.SET_NULL)
	name = attribute("name", str)

	TYPE = "external_network"
	CAP_CHILDREN = {}
	
	CUSTOM_ACTIONS = {
		"start": [ST_CREATED],
		"stop": [ST_STARTED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"site": [ST_CREATED],
		"name": [ST_CREATED, ST_STARTED],
	}
	DIRECT_ATTRS_EXCLUDE = []
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}
	CAP_CONNECTABLE = True

	class Meta:
		db_table = "tomato_external_network"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
	
	def mainElement(self):
		return self.element
	
	def modify_name(self, val):
		self.name = val

	def modify_site(self, val):
		self.site = host.getSite(val)

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

	def action_start(self):
		_host = host.select(site=self.site, elementTypes=[self.TYPE])
		fault.check(_host, "No matching host found for element %s", self.TYPE)
		attrs = self._remoteAttrs()
		self.element = _host.createElement(self.TYPE, parent=None, attrs=attrs)
		self.setState(ST_STARTED)
		
	def action_destroy(self):
		if self.element:
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["site"] = self.site.name if self.site else None
		return info
	
elements.TYPES[External_Network.TYPE] = External_Network