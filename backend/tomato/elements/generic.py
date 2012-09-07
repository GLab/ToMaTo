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
from tomato import elements, resources, host, fault
from tomato.lib.attributes import attribute #@UnresolvedImport

ST_CREATED = "created"
ST_PREPARED = "prepared"
ST_STARTED = "started"

class VMElement(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	site = models.ForeignKey(host.Site, null=True, on_delete=models.SET_NULL)
	name = attribute("name", str)
	profile = attribute("profile", str)
	template = models.ForeignKey(resources.Resource, null=True)
	
	CUSTOM_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"site": [ST_CREATED],
		"name": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"profile": [ST_CREATED, ST_PREPARED],
		"template": [ST_CREATED, ST_PREPARED],
	}
	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus"]
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}
	
	class Meta:
		abstract = True
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
		#template: None, default template
	
	def mainElement(self):
		return self.element
	
	def _template(self):
		if self.template:
			return self.template
		pref = resources.template.getPreferred(self.TYPE)
		fault.check(pref, "Failed to find template for %s", self.TYPE, fault.INTERNAL_ERROR)
		return pref

	def modify_name(self, val):
		self.name = val

	def modify_site(self, val):
		self.site = host.getSite(val)

	def modify_template(self, tmplName):
		self.template = resources.template.get(self.TYPE, tmplName)
		if self.element:
			self.element.modify({"template": self.template.name if self.template else None})

	def onChildAdded(self, iface):
		if self.element:
			iface._create()
			iface.setState(self.state)

	def onChildRemoved(self, iface):
		if self.element:
			iface._remove()
			iface.setState(self.state)

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
		_host = host.select(site=self.site, elementTypes=[self.TYPE]+self.CAP_CHILDREN.keys())
		fault.check(_host, "No matching host found for element %s", self.TYPE)
		attrs = self._remoteAttrs()
		attrs.update({
			"template": self.template.name if self.template else None,
		})
		self.element = _host.createElement(self.TYPE, parent=None, attrs=attrs, owner=self)
		self.save()
		for iface in self.getChildren():
			iface._create()
		self.element.action("prepare")
		self.setState(ST_PREPARED, True)
		
	def action_destroy(self):
		if self.element:
			self.element.action("destroy")
			for iface in self.getChildren():
				iface._remove()
			self.element.remove()
			self.element = None
		self.setState(ST_CREATED, True)

	def after_stop(self):
		for ch in self.getChildren():
			ch.triggerConnectionStop()
	
	def after_start(self):
		for ch in self.getChildren():
			ch.triggerConnectionStart()

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.name if self.template else None
		info["attrs"]["site"] = self.site.name if self.site else None
		return info


class VMInterface(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)

	CUSTOM_ACTIONS = {
		elements.REMOVE_ACTION: [ST_CREATED, ST_PREPARED]
	}
	CAP_CHILDREN = {}
	CAP_CONNECTABLE = True
	
	class Meta:
		abstract = True
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line

	def mainElement(self):
		return self.element
		
	def _create(self):
		parEl = self.getParent().element
		assert parEl
		self.element = parEl.createChild(self.TYPE, attrs={}, owner=self)
		self.save()
		
	def _remove(self):
		if self.element:
			self.element.remove()
			self.element = None
			self.save()

	def readyToConnect(self):
		return self.state == ST_STARTED

	def upcast(self):
		return self