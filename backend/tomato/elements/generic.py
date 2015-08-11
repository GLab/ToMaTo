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

from ..db import *
from ..generic import *
from ..elements import Element
from ..host.element import HostElement
from ..host.site import Site
from ..resources.profile import Profile
from ..resources.template import Template
from .. import elements, host
from ..lib.error import UserError, InternalError
import time

ST_CREATED = "created"
ST_PREPARED = "prepared"
ST_STARTED = "started"

class VMElement(Element):
	element = ReferenceField(HostElement)
	site = ReferenceField(Site)
	name = StringField()
	profile = ReferenceField(Profile)
	template = ReferenceField(Template)
	rextfvLastStarted = FloatField(default=0, db_field='rextfv_last_started')
	nextSync = FloatField(default=0, db_field='next_sync')
	lastSync = FloatField(default=0, db_field='last_sync')
	customTemplate = BooleanField(default=False, db_field='custom_template')

	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus", "timeout", "template"]
	CAP_PARENT = [None]
	DEFAULT_ATTRS = {}
	PROFILE_ATTRS = []
	
	#for every subclass which supports RexTFV: create a process which calls this function on every VMElement with  0 != next_sync < time.time()
	def updateInfo(self): 
		if self.element is None:
			return
		try:
			self.element.updateInfo()
		except:
			pass
		
		self.lastSync = time.time()
		
		#calculate next update time:
		time_passed = int(time.time()) - self.rextfvLastStarted
		if time_passed < 60*60*24: #less than one day
			self.nextSync = int(time.time()) + (time_passed / 24)
		else: # more than one day:
			self.nextSync = 0 #the process which syncs everything every hour is still active. do nothing more.
		self.save()
		
	def set_rextfv_last_started(self):
		self.rextfvLastStarted = int(time.time())
		self.nextSync = int(time.time()) + 1 #make sure sync process will be triggered.
		self.save()
	
	def init(self, topology, *args, **kwargs):
		self.state = ST_CREATED
		self.topology = topology
		self.site = self.topology.site
		self.profile = Profile.getPreferred(self.TYPE)
		InternalError.check(self.profile, code=InternalError.CONFIGURATION_ERROR, message="Failed to find profile",
			data={"type": self.TYPE})
		self.template = Template.getPreferred(self.TYPE)
		InternalError.check(self.template, code=InternalError.CONFIGURATION_ERROR, message="Failed to find template",
			data={"type": self.TYPE})
		elements.Element.init(self, topology, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.TYPE + str(self.id)
		self.save()
		self.rextfvLastStarted = 0
		self.nextSync = 0
		#template: None, default template

	@property
	def mainElement(self):
		return self.element
	
	def _nextIfaceName(self):
		ifaces = self.children
		num = 0
		while "eth%d" % num in [iface.name for iface in ifaces]:
			num += 1
		return "eth%d" % num	

	def modify_site(self, val):
		self.site = Site.get(val)

	def modify_profile(self, val):
		profile = Profile.get(self.TYPE, val)
		UserError.check(profile, code=UserError.INVALID_VALUE, message="No such profile", data={"value": val})
		if profile.restricted and not self.profile == profile:
			UserError.check(currentUser().hasFlag(Flags.RestrictedProfiles), code=UserError.DENIED,
				message="Profile is restricted")
		self.profile = profile
		if self.element:
			self.element.modify(self._profileAttrs)

	def modify_template(self, tmplName):
		template = Template.get(self.TYPE, tmplName)
		UserError.check(template, code=UserError.INVALID_VALUE, message="No such template", data={"value": tmplName})
		if template.restricted and not self.template == template:
			UserError.check(currentUser().hasFlag(Flags.RestrictedTemplates), code=UserError.DENIED,
				message="Template is restricted")
		self.template = template
		if self.element:
			self.element.modify({"template": self.template.name})

	def onChildAdded(self, iface):
		if self.element:
			iface._create()
			iface.setState(self.state)

	def onChildRemoved(self, iface):
		if self.element:
			iface._remove()
			iface.setState(self.state)

	@property
	def _profileAttrs(self):
		attrs = {}
		profile = self.profile
		profAttrs = profile.info()
		for attr in self.PROFILE_ATTRS:
			if attr in profAttrs:
				attrs[attr] = profAttrs[attr]
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
				for iface in self.children:
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
		attrs = self._remoteAttrs
		attrs.update({
			"template": self.template.name,
		})
		attrs.update(self._profileAttrs)
		self.element = _host.createElement(self.TYPE, parent=None, attrs=attrs, ownerElement=self)
		self.save()
		for iface in self.children:
			iface._create()
		self.element.action("prepare")
		self.setState(ST_PREPARED, True)
		
	def action_destroy(self):
		if isinstance(self.element, HostElement):
			try:
				self.element.action("destroy")
			except UserError:
				if self.element.state != ST_CREATED:
					raise
			for iface in self.children:
				iface._remove()
			self.element.remove()
			self.element = None
			self.customTemplate = False
		self.setState(ST_CREATED, True)
		
	def action_stop(self):
		if isinstance(self.element, HostElement):
			self.element.action("stop")
		self.setState(ST_PREPARED, True)
		self.after_stop()

	def after_rextfv_upload_use(self):
		self.set_rextfv_last_started()
		
	def after_stop(self):
		for ch in self.children:
			ch.triggerConnectionStop()
	
	def after_start(self):
		self.set_rextfv_last_started()
		for ch in self.children:
			ch.triggerConnectionStart()

	def after_upload_use(self):
		self.customTemplate = True
		self.save()

	ATTRIBUTES = Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"site": StatefulAttribute(get=lambda self: self.site.name if self.site else None, set=modify_site, writableStates=[ST_CREATED]),
		"profile": StatefulAttribute(get=lambda self: self.profile.name if self.profile else None, set=modify_profile, writableStates=[ST_CREATED, ST_PREPARED]),
		"template": StatefulAttribute(get=lambda self: self.template.name if self.template else None, set=modify_template, writableStates=[ST_CREATED]),
		"name": Attribute(field=name, label="Name"),
		"info_last_sync": Attribute(field=lastSync, readOnly=True)
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element._checkRemove, allowedStates=[ST_CREATED]),
		"stop": StatefulAction(action_stop, allowedStates=[ST_STARTED], stateChange=ST_PREPARED),
		"prepare": StatefulAction(action_prepare, allowedStates=[ST_CREATED], stateChange=ST_PREPARED),
		"destroy": StatefulAction(action_destroy, allowedStates=[ST_PREPARED], stateChange=ST_CREATED),
		"change_template": StatefulAction(action_change_template, allowedStates=[ST_CREATED, ST_PREPARED])
	})


class VMInterface(Element):
	"""
	:type parent: VMElement
	"""
	parent = Element.parent
	element = ReferenceField(HostElement)
	name = StringField(regex="^eth[0-9]+$")

	CAP_CHILDREN = {}
	CAP_CONNECTABLE = True
	DIRECT_ATTRS_EXCLUDE=["timeout"]
	
	SAME_HOST_AFFINITY = -20 #we want connected elements on different hosts to lower host load	
	
	def init(self, *args, **kwargs):
		self.state = ST_CREATED
		elements.Element.init(self, *args, **kwargs) #no id and no attrs before this line
		if not self.name:
			self.name = self.parent._nextIfaceName()

	@property
	def mainElement(self):
		return self.element

	def _create(self):
		parEl = self.parent.element
		assert parEl
		attrs = self._remoteAttrs
		self.element = parEl.createChild(self.TYPE, attrs=attrs, ownerElement=self)
		self.save()
		
	def _remove(self, recurse=None):
		if isinstance(self.element, HostElement):
			self.element.remove()
			self.element = None
			self.save()

	@property
	def readyToConnect(self):
		return self.state == ST_STARTED

	ATTRIBUTES = Element.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"name": Attribute(field=name, label="Name"),
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element._checkRemove, allowedStates=[ST_CREATED, ST_PREPARED])
	})


class ConnectingElement(object):
	"""
	:type children: list of Element
	"""
	parent = Element.parent
	children = Element.children
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
			return self.parent.getLocationData(maxDepth=maxDepth)
		els = set()
		for ch in self.children:
			if ch.connection:
				els.update(ch.connectedElement.getLocationData(maxDepth=maxDepth-1))
		return els
	
from .. import currentUser
from ..auth import Flags
