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
from .. import elements, resources, host
from ..resources import profile as r_profile, template as r_template
from ..lib.attributes import Attr, attribute #@UnresolvedImport
from ..lib import attributes #@UnresolvedImport
from ..lib.error import UserError, InternalError
import time

ST_CREATED = "created"
ST_PREPARED = "prepared"
ST_STARTED = "started"

class VMElement(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	site_attr = Attr("site", desc="Site", type="str", null=True, states=[ST_CREATED])
	site = models.ForeignKey(host.Site, null=True, on_delete=models.SET_NULL)
	name_attr = Attr("name", desc="Name", type="str")
	name = name_attr.attribute()
	profile_attr = Attr("profile", desc="Profile", type="str", null=True, states=[ST_CREATED, ST_PREPARED])
	profile = models.ForeignKey(r_profile.Profile, null=True, on_delete=models.SET_NULL)
	template_attr = Attr("template", desc="Template", type="str", null=True, states=[ST_CREATED])
	template = models.ForeignKey(r_template.Template, null=True, on_delete=models.SET_NULL)
	rextfv_last_started = models.FloatField(default = 0) #whenever an action which may trigger the rextfv autostarted script is done, set this to current time. set by self.set_rextfv_last_started
	next_sync = models.FloatField(default = 0, db_index=True) #updated on updateInfo. If != 0: will be synced when current time >= self.next_sync.
	last_sync = attributes.attribute("last_sync", float, 0)
	custom_template = attribute("custom_template", bool, default=False) #is set to true after an image has been uploaded
	
	CUSTOM_ACTIONS = {
		"stop": [ST_STARTED],
		"prepare": [ST_CREATED],
		"destroy": [ST_PREPARED],
		"change_template": [ST_CREATED, ST_PREPARED],
		elements.REMOVE_ACTION: [ST_CREATED],
	}
	CUSTOM_ATTRS = {
		"site": site_attr,
		"name": name_attr,
		"profile": profile_attr,
		"template": template_attr,
	}
	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus", "timeout", "template"]
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}
	
	class Meta:
		abstract = True
		
		
	#for every subclass which supports RexTFV: create a process which calls this function on every VMElement with  0 != next_sync < time.time()
	def updateInfo(self): 
		if self.element is None:
			return
		
		try:
			self.element.updateInfo()
		except:
			pass
		
		self.last_sync = time.time()
		
		#calculate next update time:
		time_passed = int(time.time()) - self.rextfv_last_started
		if time_passed < 60*60*24: #less than one day
			self.next_sync = int(time.time()) + (time_passed / 24)
		else: # more than one day:
			self.next_sync = 0 #the process which syncs everything every hour is still active. do nothing more.
		self.save()
		
	def set_rextfv_last_started(self):
		self.rextfv_last_started = int(time.time())
		self.next_sync = int(time.time()) + 1 #make sure sync process will be triggered.
		self.save()
	
	def init(self, topology, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		self.topology = topology
		self.site = self.topology.site
		elements.Element.init(self, topology, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
		self.rextfv_last_started = 0
		self.next_sync = 0
		#template: None, default template
	
	def mainElement(self):
		return self.element
	
	def _nextIfaceName(self):
		ifaces = self.getChildren()
		num = 0
		while "eth%d" % num in [iface.name for iface in ifaces]:
			num += 1
		return "eth%d" % num	
	
	def _profile(self):
		if self.profile:
			return self.profile
		pref = resources.profile.getPreferred(self.TYPE)
		InternalError.check(pref, code=InternalError.CONFIGURATION_ERROR, message="Failed to find profile",
			data={"type": self.TYPE})
		return pref

	def _template(self):
		if self.template:
			return self.template
		pref = resources.template.getPreferred(self.TYPE)
		InternalError.check(pref, code=InternalError.CONFIGURATION_ERROR, message="Failed to find template",
			data={"type": self.TYPE})
		return pref

	def modify_name(self, val):
		self.name = val

	def modify_site(self, val):
		self.site = host.getSite(val)

	def modify_profile(self, val):
		profile = resources.profile.get(self.TYPE, val)
		UserError.check(profile, code=UserError.INVALID_VALUE, message="No such profile", data={"value": val})
		if profile.restricted and not self.profile == profile:
			UserError.check(currentUser().hasFlag(Flags.RestrictedProfiles), code=UserError.DENIED,
				message="Profile is restricted")
		self.profile = profile
		if self.element:
			self.element.modify(self._profileAttrs())

	def modify_template(self, tmplName):
		template = resources.template.get(self.TYPE, tmplName)
		UserError.check(template, code=UserError.INVALID_VALUE, message="No such template", data={"value": tmplName})
		if template.restricted and not self.template == template:
			UserError.check(currentUser().hasFlag(Flags.RestrictedTemplates), code=UserError.DENIED,
				message="Template is restricted")
		self.template = template
		if self.element:
			self.element.modify({"template": self._template().name})

	def onChildAdded(self, iface):
		if self.element:
			iface._create()
			iface.setState(self.state)

	def onChildRemoved(self, iface):
		if self.element:
			iface._remove()
			iface.setState(self.state)

	def _profileAttrs(self):
		attrs = {}
		profile = self._profile()
		for attr in self.PROFILE_ATTRS:
			if profile.getAttribute(attr):
				attrs[attr] = profile.getAttribute(attr)
		return attrs

	def onError(self, exc):
		if self.element:
			try:
				self.element.updateInfo()
			except UserError, err:
				if err.code == UserError.ENTITY_DOES_NOT_EXIST:
					self.element.state = ST_CREATED
			self.setState(self.element.state, True)
			if self.state == ST_CREATED:
				if self.element:
					self.element.remove()
				for iface in self.getChildren():
					iface._remove()
				self.element = None
			self.save()
			
	def action_change_template(self, tmplName):
		self.modify_template(tmplName)

	def action_prepare(self):
		hPref, sPref = self.getLocationPrefs()
		_host = host.select(site=self.site, elementTypes=[self.TYPE]+self.CAP_CHILDREN.keys(), hostPrefs=hPref, sitePrefs=sPref)
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element",
			data={"type": self.TYPE})
		attrs = self._remoteAttrs()
		attrs.update({
			"template": self._template().name,
		})
		attrs.update(self._profileAttrs())
		self.element = _host.createElement(self.TYPE, parent=None, attrs=attrs, ownerElement=self)
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
			self.custom_template = False
		self.setState(ST_CREATED, True)
		
	def action_stop(self):
		if self.element:
			self.element.action("stop")
		self.setState(ST_PREPARED, True)

	def after_rextfv_upload_use(self):
		self.set_rextfv_last_started()
		
	def after_stop(self):
		for ch in self.getChildren():
			ch.triggerConnectionStop()
	
	def after_start(self):
		self.set_rextfv_last_started()
		for ch in self.getChildren():
			ch.triggerConnectionStart()

	def after_upload_use(self):
		self.custom_template = True
		self.save()

	def upcast(self):
		return self

	def info(self):
		info = elements.Element.info(self)
		info["info_sync_date"] = self.last_sync
		info["attrs"]["template"] = self._template().name
		info["attrs"]["profile"] = self._profile().name
		info["attrs"]["site"] = self.site.name if self.site else None
		info["attrs"]["host"] = self.element.host.name if self.element else None
		info["attrs"]["host_info"] = {
									'address':			self.element.host.address if self.element else None,
									'problems': 		self.element.host.problems() if self.element else None,
									'site':				self.element.host.site.name if self.element else None,
									'fileserver_port': 	self.element.host.hostInfo.get('fileserver_port', None) if self.element else None
									}
		return info


class VMInterface(elements.Element):
	element = models.ForeignKey(host.HostElement, null=True, on_delete=models.SET_NULL)
	name_attr = Attr("name", desc="Name", type="str", regExp="^eth[0-9]+$")
	name = name_attr.attribute()

	CUSTOM_ACTIONS = {
		elements.REMOVE_ACTION: [ST_CREATED, ST_PREPARED]
	}
	CAP_CHILDREN = {}
	CAP_CONNECTABLE = True
	DIRECT_ATTRS_EXCLUDE=["timeout"]
	
	SAME_HOST_AFFINITY = -20 #we want connected elements on different hosts to lower host load	
	
	class Meta:
		abstract = True
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.getParent()._nextIfaceName()

	def mainElement(self):
		return self.element
		
	def _create(self):
		parEl = self.getParent().element
		assert parEl
		attrs = self._remoteAttrs()
		self.element = parEl.createChild(self.TYPE, attrs=attrs, ownerElement=self)
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
	

class ConnectingElement:
	def getLocationData(self, maxDepth=3):
		"""
		Determines where this element is located and how much it wants other elements to be close by.
		Elements that are mainly connections other elements might overwrite this and use location
		data of these elements instead.
		Since this calculation can get stuck in a loop the depth is limited by a parameter. The
		maxDepth is decremented each time the calculation spans another element group.
		 
		@param maxDepth: Parameter limiting the maximal depth of calculation
		"""
		if maxDepth <= 0:
			return []
		if self.parent:
			return self.parent.upcast().getLocationData(maxDepth=maxDepth)
		els = set()
		for ch in self.getChildren():
			if ch.connection:
				els.update(ch.getConnectedElement().getLocationData(maxDepth=maxDepth-1))
		return els
	
from .. import currentUser
from ..auth import Flags
