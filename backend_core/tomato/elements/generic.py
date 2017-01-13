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
from ..lib.constants import StateName, ActionName, TypeTechTrans
from ..lib.references import Reference

ST_CREATED = StateName.CREATED
ST_PREPARED = StateName.PREPARED
ST_STARTED = StateName.STARTED

class VMElement(Element):
	element = ReferenceField(HostElement, reverse_delete_rule=NULLIFY)
	site = ReferenceField(Site, reverse_delete_rule=NULLIFY)
	name = StringField()
	profile = ReferenceField(Profile, reverse_delete_rule=DENY)
	template = ReferenceField(Template, reverse_delete_rule=NULLIFY)
	rextfvLastStarted = FloatField(default=0, db_field='rextfv_last_started')
	nextSync = FloatField(default=0, db_field='next_sync')
	lastSync = FloatField(default=0, db_field='last_sync')
	customTemplate = BooleanField(default=False, db_field='custom_template')

	meta = {
		'allow_inheritance': True,
		'indexes': [
			'nextSync'
		]
	}

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
		if val:
			site = Site.get(val)
			UserError.check(site, code=UserError.ENTITY_DOES_NOT_EXIST, message="site does not exist", data={"site": val})
			self.site = site
		else:
			self.site = None

	def modify_profile(self, val):
		profile = Profile.get(self.TYPE, val)
		UserError.check(profile, code=UserError.INVALID_VALUE, message="No such profile", data={"value": val})
		self.profile = profile
		if self.element:
			self.element.modify(**self._profileAttrs)

	def modify_template(self, tmplName):
		template = Template.get(self.TYPE, tmplName)
		UserError.check(template, code=UserError.INVALID_VALUE, message="No such template", data={"value": tmplName})
		self.template = template
		template.on_selected()
		if self.element:
			self.element.modify(template=self.template.name)

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
			
	def action_change_template(self, template):
		self.modify_template(template)

	def _get_elementTypeConfigurations(self):
		"""
		get element type configurations for action_prepare()
		:return:
		"""
		return [[self.TYPE] + self.CAP_CHILDREN.keys()]

	def _select_tech(self, _host):
		return self.type

	def action_prepare(self):
		hPref, sPref = self.getLocationPrefs()
		_host = host.select(site=self.site if self.site else self.topology.site, elementTypeConfigurations=self._get_elementTypeConfigurations(), hostPrefs=hPref, sitePrefs=sPref, template=self.template)  # fixme: use tech
		UserError.check(_host, code=UserError.NO_RESOURCES, message="No matching host found for element",
			data={"type": self.TYPE, "configs": self._get_elementTypeConfigurations()})
		attrs = self._remoteAttrs
		type_ = self._select_tech(_host)
		attrs.update({
			"template": self.template.name
		})
		attrs.update(self._profileAttrs)
		self.element = _host.createElement(type_, parent=None, attrs=attrs, ownerElement=self)
		self.save()
		for iface in self.children:
			iface._create()
		self.element.action(ActionName.PREPARE)
		self.setState(ST_PREPARED, True)
		
	def action_destroy(self):
		if isinstance(self.element, HostElement):
			try:
				if self.state == ST_STARTED:
					self.element.action(ActionName.STOP)
				self.element.action(ActionName.DESTROY)
			except UserError:
				if self.element.state != ST_CREATED:
					raise
			except:
				pass
			for iface in self.children:
				iface.triggerConnectionStop()
				iface._remove()
			self.element.remove()
			self.element = None
			self.customTemplate = False
		self.setState(ST_CREATED, True)
		
	def action_stop(self):
		if isinstance(self.element, HostElement):
			self.element.action(ActionName.STOP)
		self.setState(ST_PREPARED, True)
		for ch in self.children:
			ch.triggerConnectionStop()

	def action_start(self):
		if self.state == ST_CREATED:
			self.action_prepare()
		self.element.action(ActionName.START)
		self.setState(ST_STARTED, True)

	def after_rextfv_upload_use(self):
		self.set_rextfv_last_started()

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
		"info_last_sync": Attribute(field=lastSync, readOnly=True,label="Last synchronization"),
		"info_next_sync": Attribute(field=nextSync, readOnly=True,label="Next synchronization")
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element.checkRemove, allowedStates=[ST_CREATED]),
		ActionName.START: StatefulAction(action_start, allowedStates=[ST_CREATED, ST_PREPARED], stateChange=ST_STARTED),
		ActionName.STOP: StatefulAction(action_stop, allowedStates=[ST_STARTED], stateChange=ST_PREPARED),
		ActionName.PREPARE: StatefulAction(action_prepare, check=Element.checkTopologyTimeout, allowedStates=[ST_CREATED], stateChange=ST_PREPARED),
		ActionName.DESTROY: StatefulAction(action_destroy, allowedStates=[ST_PREPARED, ST_STARTED], stateChange=ST_CREATED),
		ActionName.CHANGE_TEMPLATE: StatefulAction(action_change_template, allowedStates=[ST_CREATED, ST_PREPARED])
	})


class MultiTechVMElement(VMElement):
	TECHS = []
	tech = StringField(required=False, default=None)

	def modify_tech(self, tech):
		if tech is not None:
			UserError.check(tech in self.TECHS, UserError.INVALID_VALUE, "tech '%s' not supported for type '%s'" % (tech, self.TYPE), data={"tech": tech, "type": self.TYPE})
		self.tech = tech

	def _get_elementTypeConfigurations(self):
		if self.tech:
			return [[self.tech, TypeTechTrans.TECH_TO_CHILD_TECH[self.tech]]]
		return [[k, v] for k, v in TypeTechTrans.TECH_TO_CHILD_TECH.iteritems()]

	def get_tech_attribute(self):
		return self.element.type if self.element else self.tech

	def _select_tech(self, _host):
		if self.tech:
			return self.tech
		else:
			for tech in self.TECHS:
				if tech in _host.elementTypes:
					return tech
		raise InternalError(code=InternalError.ASSERTION, message="selected host doesn't match element requirement",
		                    data={"type": self.TYPE, "host": _host.name, "ref": Reference.host(_host.name)})

	ATTRIBUTES = VMElement.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"tech": StatefulAttribute(get=lambda self: self.get_tech_attribute(), label="Tech", set=modify_tech, writableStates=[ST_CREATED], schema=schema.Identifier())
	})

class VMInterface(Element):
	"""
	:type parent: VMElement
	"""
	parent = Element.parent
	element = ReferenceField(HostElement, reverse_delete_rule=NULLIFY)
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

	@property
	def _create_type(self):
		return self.TYPE

	def _create(self):
		parEl = self.parent.element
		assert parEl
		attrs = self._remoteAttrs
		self.element = parEl.createChild(self._create_type, attrs=attrs, ownerElement=self)
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
		"name": StatefulAttribute(field=name, label="Name", schema=schema.String(regex="^eth[0-9]+$"), writableStates=[ST_PREPARED, ST_CREATED]),
	})

	ACTIONS = Element.ACTIONS.copy()
	ACTIONS.update({
		Entity.REMOVE_ACTION: StatefulAction(Element._remove, check=Element.checkRemove, allowedStates=[ST_CREATED, ST_PREPARED])
	})


class MultiTechVMInterface(VMInterface):
	TECHS = []

	def get_tech_attribute(self):
		if self.parent:
			parent_tech = self.parent.get_tech_attribute()
		else:
			parent_tech = None

		if parent_tech:
			return TypeTechTrans.TECH_TO_CHILD_TECH[parent_tech]
		else:
			return None

	@property
	def _create_type(self):
		return self.get_tech_attribute()

	ATTRIBUTES = VMInterface.ATTRIBUTES.copy()
	ATTRIBUTES.update({
		"tech": Attribute(get=lambda self: self.get_tech_attribute(), label="Tech", readOnly=True, schema=schema.Identifier()),
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

