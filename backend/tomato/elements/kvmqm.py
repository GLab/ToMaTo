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

DOC = """
"""

class KVMQM(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	site = models.ForeignKey(host.Site, null=True, on_delete=models.SET_NULL)

	name = attribute("name", str)
	profile = attribute("profile", str)
	template = models.ForeignKey(resources.Resource, null=True)
	
	vncport = attribute("vncport", int)
	vncpassword = attribute("vncpassword", str)	

	ST_CREATED = "created"
	ST_PREPARED = "prepared"
	ST_STARTED = "started"
	TYPE = "kvmqm"
	CAP_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		"upload_grant": [ST_PREPARED],
		"upload_use": [ST_PREPARED],
		"download_grant": [ST_PREPARED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CAP_NEXT_STATE = {
		"prepare": ST_PREPARED,
		"destroy": ST_CREATED,
		"start": ST_STARTED,
		"stop": ST_PREPARED,
	}	
	CAP_ATTRS = {
		"site": [ST_CREATED],
		"name": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"profile": [ST_CREATED, ST_PREPARED],
		"template": [ST_CREATED, ST_PREPARED],
	}
	CAP_CHILDREN = {
		"kvmqm_interface": [ST_CREATED, ST_PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}
	DOC = DOC
	
	class Meta:
		db_table = "tomato_kvmqm"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
		#template: None, default template
	
	def _template(self):
		if self.template:
			return self.template
		pref = resources.template.getPreferred(self.TYPE)
		fault.check(pref, "Failed to find template for %s", self.TYPE, fault.INTERNAL_ERROR)
		return pref

	def getHostElements(self):
		return [self.element] if self.element else []

	def modify_name(self, val):
		self.name = val

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
			self.element.updateInfo()
			self.setState(self.element.state, True)
			if self.state == self.ST_CREATED:
				if self.element:
					self.element.remove()
				for iface in self.getChildren():
					iface._remove()
				self.element = None
			self.save()

	def action_prepare(self):
		_host = host.select(site=self.site, elementTypes=[self.TYPE]+self.CAP_CHILDREN.keys())
		fault.check(_host, "No matching host found for element %s", self.TYPE)
		self.element = _host.createElement(self.TYPE, parent=None, attrs={
			"template": self.template.name if self.template else None,
		})
		self.save()
		for iface in self.getChildren():
			iface._create()
		self.element.action("prepare")
		self.setState(self.ST_PREPARED, True)
		
	def action_destroy(self):
		if self.element:
			self.element.action("destroy")
			for iface in self.getChildren():
				iface._remove()
			self.element.remove()
			self.element = None
		self.setState(self.ST_CREATED, True)

	def action_start(self):
		self.element.action("start")
		self.setState(self.ST_STARTED, True)
				
	def action_stop(self):
		self.element.action("stop")
		self.setState(self.ST_PREPARED, True)

	def action_upload_grant(self):
		return self.element.action("upload_grant")
		
	def action_upload_use(self):
		return self.element.action("upload_use")
		
	def action_download_grant(self):
		return self.element.action("download_grant")
	
	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["attrs"]["template"] = self.template.name if self.template else None
		info["attrs"]["site"] = self.site.name if self.site else None
		if self.element:
			info["attrs"].update(self.element.attrs)
		return info


DOC_IFACE = """
"""

class KVMQM_Interface(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)

	TYPE = "kvmqm_interface"
	CAP_ACTIONS = {
		elements.REMOVE_ACTION: [KVMQM.ST_CREATED, KVMQM.ST_PREPARED]
	}
	CAP_NEXT_STATE = {}	
	CAP_ATTRS = {}
	CAP_CHILDREN = {}
	CAP_PARENT = [KVMQM.TYPE]
	DOC = DOC_IFACE
	
	class Meta:
		db_table = "tomato_kvmqm_interface"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = KVMQM.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		assert isinstance(self.getParent(), KVMQM)

	def getHostElements(self):
		return [self.element] if self.element else []
		
	def _create(self):
		parEl = self.getParent().element
		assert parEl
		self.element = parEl.createChild(self.TYPE, attrs={})
		self.save()
		
	def _remove(self):
		if self.element:
			self.element.remove()
			self.element = None
			self.save()

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		if self.element:
			info["attrs"].update(self.element.attrs)
		return info

elements.TYPES[KVMQM.TYPE] = KVMQM
elements.TYPES[KVMQM_Interface.TYPE] = KVMQM_Interface