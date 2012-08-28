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

class OpenVZ(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	site = models.ForeignKey(host.Site, null=True, on_delete=models.SET_NULL)

	name = attribute("name", str)
	profile = attribute("profile", str)
	template = models.ForeignKey(resources.Resource, null=True)
	
	vncport = attribute("vncport", int)
	vncpassword = attribute("vncpassword", str)	
	rootpassword = attribute("rootpassword", str)
	hostname = attribute("hostname", str)	
	gateway4 = attribute("gateway4", str)	
	gateway6 = attribute("gateway6", str)	

	ST_CREATED = "created"
	ST_PREPARED = "prepared"
	ST_STARTED = "started"
	TYPE = "openvz"
	CAP_ACTIONS = {
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"start": [ST_PREPARED],
		"stop": [ST_STARTED],
		"upload_grant": [ST_PREPARED],
		"upload_use": [ST_PREPARED],
		"download_grant": [ST_PREPARED],
		"execute": [ST_STARTED],
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
		"rootpassword": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"hostname": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"gateway4": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"gateway6": [ST_CREATED, ST_PREPARED, ST_STARTED],
		"template": [ST_CREATED, ST_PREPARED],
	}
	CAP_CHILDREN = {
		"openvz_interface": [ST_CREATED, ST_PREPARED],
	}
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}
	DOC = DOC
	
	class Meta:
		db_table = "tomato_openvz"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = self.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		if not self.hostname:
			self.hostname = self.topology.name + "_" + self.name
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

	def modify_rootpassword(self, val):
		self.rootpassword = val
		if self.element:
			self.element.modify({"rootpassword": val})
	
	def modify_hostname(self, val):
		self.hostname = val
		if self.element:
			self.element.modify({"hostname": val})

	def modify_gateway4(self, val):
		self.gateway4 = val
		if self.element:
			self.element.modify({"gateway4": val})

	def modify_gateway6(self, val):
		self.gateway6 = val
		if self.element:
			self.element.modify({"gateway4": val})
	
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
			"rootpassword": self.rootpassword,
			"hostname": self.hostname,	
			"gateway4": self.gateway4,	
			"gateway6": self.gateway6,
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
	
	def action_execute(self, cmd):
		return self.element.action("execute", {"cmd": cmd})

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

class OpenVZ_Interface(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)

	ip4address = attribute("ip4address", str, "")
	ip6address = attribute("ip6address", str, "")
	use_dhcp = attribute("use_dhcp", bool, default=False)

	TYPE = "openvz_interface"
	CAP_ACTIONS = {
		elements.REMOVE_ACTION: [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED]
	}
	CAP_NEXT_STATE = {}	
	CAP_ATTRS = {
		"ip4address": [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED, OpenVZ.ST_STARTED],
		"ip6address": [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED, OpenVZ.ST_STARTED],
		"use_dhcp": [OpenVZ.ST_CREATED, OpenVZ.ST_PREPARED, OpenVZ.ST_STARTED],
	}
	CAP_CHILDREN = {}
	CAP_PARENT = [OpenVZ.TYPE]
	DOC = DOC_IFACE
	
	class Meta:
		db_table = "tomato_openvz_interface"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = OpenVZ.ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		assert isinstance(self.getParent(), OpenVZ)

	def getHostElements(self):
		return [self.element] if self.element else []
		
	def modify_ip4address(self, val):
		self.ip4address = val
		if self.element:
			self.element.modify({"ip4address": val})

	def modify_ip6address(self, val):
		self.ip6address = val
		if self.element:
			self.element.modify({"ip6address": val})

	def modify_use_dhcp(self, val):
		self.use_dhcp = val
		if self.element:
			self.element.modify({"use_dhcp": val})
	
	def _create(self):
		parEl = self.getParent().element
		assert parEl
		self.element = parEl.createChild(self.TYPE, attrs={
			"ip4address": self.ip4address,
			"ip6address": self.ip6address,
			"use_dhcp": self.use_dhcp,
		})
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

elements.TYPES[OpenVZ.TYPE] = OpenVZ
elements.TYPES[OpenVZ_Interface.TYPE] = OpenVZ_Interface