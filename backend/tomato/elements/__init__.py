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

import threading
from django.db import models

from ..connections import Connection
from ..auth import Flags
from ..auth.permissions import Permissions, PermissionMixin, Role
from ..topology import Topology
from ..lib import db, attributes, logging #@UnresolvedImport
from ..accounting import UsageStatistics
from ..lib.decorators import *
from ..lib.cache import cached #@UnresolvedImport
from ..lib.error import UserError, InternalError

TYPES = {}
REMOVE_ACTION = "(remove)"

LOCKS = {}
LOCKS_LOCK = threading.RLock()

def getLock(obj):
	with LOCKS_LOCK:
		if not obj.id in LOCKS:
			LOCKS[obj.id] = threading.RLock()
		return LOCKS[obj.id]
	
def removeLock(obj):
	with LOCKS_LOCK:
		with getLock(obj):
			del LOCKS[obj.id]

class Element(PermissionMixin, db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
	topology = models.ForeignKey(Topology, null=False, related_name="elements")
	type = models.CharField(max_length=30, validators=[db.nameValidator], choices=[(t, t) for t in TYPES.keys()]) #@ReservedAssignment
	state = models.CharField(max_length=20, validators=[db.nameValidator])
	parent = models.ForeignKey('self', null=True, related_name='children')
	connection = models.ForeignKey(Connection, null=True, on_delete=models.SET_NULL, related_name='elements')
	permissions = models.ForeignKey(Permissions, null=False)
	totalUsage = models.OneToOneField(UsageStatistics, null=True, related_name='+', on_delete=models.SET_NULL)
	attrs = db.JSONField()
	#host_elements: [host.HostElement]
	#host_connections: [host.HostConnections]
	
	DIRECT_ACTIONS = True
	DIRECT_ACTIONS_EXCLUDE = []
	CUSTOM_ACTIONS = {}
	
	DIRECT_ATTRS = True
	DIRECT_ATTRS_EXCLUDE = []
	CUSTOM_ATTRS = {}
	
	HOST_TYPE = ""
	
	DOC = ""
	CAP_CHILDREN = {}
	CAP_PARENT = []
	CAP_CONNECTABLE = False
	DEFAULT_ATTRS = {}
	
	# whether neighboring elements should be on the same host/site
	SAME_HOST_AFFINITY = -10 #distribute load
	SAME_SITE_AFFINITY = 20 #keep traffic local and latencies low
	
	class Meta:
		pass

	def init(self, topology, parent=None, attrs=None):
		if not attrs: attrs = {}
		topology.checkRole(Role.manager)
		if parent:
			UserError.check(parent.type in self.CAP_PARENT, code=UserError.INVALID_VALUE,
				message="Parent type not allowed for this type", data={"parent_type": parent.type, "type": self.type})
			UserError.check(self.type in parent.CAP_CHILDREN, code=UserError.INVALID_VALUE,
				message="Parent does not allow children of this type", data={"parent_type": parent.type, "type": self.type})
			UserError.check(parent.state in parent.CAP_CHILDREN[self.type], code=UserError.INVALID_STATE,
				message="Parent does not allow children of this type in its current state",
				data={"parent_type": parent.type, "type": self.type, "parent_state": parent.state})
		else:
			UserError.check(None in self.CAP_PARENT, code=UserError.INVALID_CONFIGURATION, message="Type needs parent",
				data={"type": self.type})
		self.topology = topology
		self.permissions = topology.permissions
		self.parent = parent
		self.attrs = dict(self.DEFAULT_ATTRS)
		self.totalUsage = UsageStatistics.objects.create()
		self.save()
		self.modify(attrs)

	def _saveAttributes(self):
		pass #disable automatic attribute saving

	def upcast(self):
		"""
		This method returns an instance of this element with the highest order
		class that it possesses. Due to a limitation of the database backend,
		all loaded objects are of the type that has been used to load them.
		In order to get to their actual type this method must be called.
		
		Classes inheriting from this class should overwrite this method to 
		return self.
		"""
		try:
			return getattr(self, self.type).reload()
		except Exception, exc:
			raise InternalError(code=InternalError.UPCAST, message="Failed to cast element to type %s" % self.type,
				data={"id": self.id, "exception": repr(exc)})

	def hasParent(self):
		return not self.parent is None

	def mainElement(self):
		return None

	def remoteType(self):
		return self.HOST_TYPE or self.type

	def _remoteAttrs(self):
		caps = host.getElementCapabilities(self.remoteType())
		allowed = caps["attrs"].keys() if caps else []
		attrs = {}
		for key, value in self.attrs.iteritems():
			if key in allowed:
				attrs[key] = value
		return attrs

	def checkState(self):
		if self.mainElement():
			self.state = self.mainElement().state
			self.save()

	def checkModify(self, attrs):
		"""
		Checks whether the attribute change can succeed before changing the
		attributes.
		If checks whether the attributes are listen in CAP_ATTRS and if the
		current object state is listed in CAP_ATTRS[NAME].
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""
		self.checkRole(Role.manager)
		mel = self.mainElement()
		direct = []
		if self.DIRECT_ATTRS:
			if mel:
				direct = mel.getAllowedAttributes().keys()
			else:
				caps = host.getElementCapabilities(self.remoteType())
				direct = caps["attrs"].keys() if caps else []
		for key in attrs.keys():
			if key in direct and not key in self.DIRECT_ATTRS_EXCLUDE:
				continue
			if key.startswith("_"):
				continue
			UserError.check(key in self.CUSTOM_ATTRS, code=UserError.UNSUPPORTED_ATTRIBUTE,
				message="Unsupported attribute", data={"type": self.type, "attribute": key, "id": self.id})
			self.CUSTOM_ATTRS[key].check(self, attrs[key])
		
	def modify(self, attrs):
		"""
		Sets the given attributes to their given values. This method first
		checks if the change can be made using checkModify() and then executes
		the attribute changes by calling modify_KEY(VALUE) for each key/value
		pair in attrs. After calling all these modify_KEY methods, it will save
		the object.
		
		Classes inheriting from this class should only implement the modify_KEY
		methods and not touch this method.  
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""
		with getLock(self):
			return self._modify(attrs)

	@db.commit_after
	def _modify(self, attrs):
		self.checkModify(attrs)
		logging.logMessage("modify", category="element", id=self.id, attrs=attrs)
		try:
			directAttrs = {}
			for key, value in attrs.iteritems():
				if key in self.CUSTOM_ATTRS:
					getattr(self, "modify_%s" % key)(value)
				else:
					if key.startswith("_"):
						self.setAttribute(key, value)
					else:
						directAttrs[key] = value
			if directAttrs:
				mel = self.mainElement()
				if mel:
					mel.modify(directAttrs)
				self.setAttributes(directAttrs)					
		except Exception, exc:
			self.onError(exc)
			raise
		self.save()
		logging.logMessage("info", category="element", id=self.id, info=self.info())			
	
	def checkAction(self, action):
		"""
		Checks if the action can be executed. This method checks if the action
		is listed in CAP_ACTIONS and if the current state is listed in 
		CAP_ACTIONS[action].
		
		@param action: Action to check
		@type action: str
		"""
		self.checkRole(Role.manager)
		if action in ["prepare", "start", "upload_grant"]:
			UserError.check(not currentUser().hasFlag(Flags.OverQuota), code=UserError.DENIED, message="Over quota")
			UserError.check(self.topology.timeout > time.time(), code=UserError.TIMED_OUT, message="Topology has timed out")
		if self.DIRECT_ACTIONS and not action in self.DIRECT_ACTIONS_EXCLUDE:
			mel = self.mainElement()
			if mel and action in mel.getAllowedActions():
				return
			if mel:
				mel.updateInfo()
				self.checkState()
			if mel and action in mel.getAllowedActions():
				return
		UserError.check(action in self.CUSTOM_ACTIONS, code=UserError.UNSUPPORTED_ACTION, message="Unsupported action",
			data={"type": self.type, "action": action, "state": self.state, "id": self.id})
		UserError.check(self.state in self.CUSTOM_ACTIONS[action], code=UserError.INVALID_STATE,
			message="Action can not be executed in the current state",
			data={"action": action, "type": self.type, "state": self.state, "id": self.id})
	
	def action(self, action, params={}):
		"""
		Executes the action with the given parameters. This method first
		checks if the action is possible using checkAction() and then executes
		the action by calling action_ACTION(**params). After calling the action
		method, it will save the object.
		
		Classes inheriting from this class should only implement the 
		action_ACTION method and not touch this method. 
		
		@param action: Name of the action
		@type action: str
		@param params: Parameters for the action
		@type params: dict
		"""
		with getLock(self):
			self.reload()
			return self._action(action, params)

		
	@db.commit_after
	def _action(self, action, params):
		self.checkAction(action)
		logging.logMessage("action start", category="element", id=self.id, action=action, params=params)
		try:
			if hasattr(self, "before_%s" % action):
				getattr(self, "before_%s" % action)(**params)
			if action in self.CUSTOM_ACTIONS:
				res = getattr(self, "action_%s" % action)(**params)
			else:
				mel = self.mainElement()
				assert mel
				res = mel.action(action, params)
				self.setState(mel.state, True)
			if hasattr(self, "after_%s" % action):
				getattr(self, "after_%s" % action)(**params)
		except Exception, exc:
			self.onError(exc)
			raise
		self.save()
		logging.logMessage("action end", category="element", id=self.id, action=action, params=params, result=res)
		logging.logMessage("info", category="element", id=self.id, info=self.info())					
		return res

	def checkRemove(self, recurse=True):
		self.checkRole(Role.manager)
		UserError.check(recurse or self.children.empty(), code=UserError.NOT_EMPTY, message="Cannot remove element with children")
		UserError.check(not REMOVE_ACTION in self.CUSTOM_ACTIONS or self.state in self.CUSTOM_ACTIONS[REMOVE_ACTION],
			code=UserError.INVALID_STATE, message="Element can not be removed in its current state",
			data={"type": self.type, "state": self.state, "id": self.id})
		for ch in self.getChildren():
			ch.checkRemove(recurse=recurse)
		if self.connection:
			self.getConnection().checkRemove()

	def setState(self, state, recursive=False):
		if recursive:
			for ch in self.getChildren():
				ch.setState(state, True)
		self.state = state
		self.save()

	def remove(self, recurse=True):
		with getLock(self):
			self._removeLocked(recurse)
		removeLock(self)
			
	def _removeLocked(self, recurse):
		self.checkRemove(recurse)
		logging.logMessage("info", category="topology", id=self.id, info=self.info())
		logging.logMessage("remove", category="topology", id=self.id)
		if self.parent:
			self.getParent().onChildRemoved(self)
		for ch in self.getChildren():
			ch.remove(recurse=True)
		if self.connection:
			self.getConnection().remove()
		self.totalUsage.remove()
		#not deleting permissions, the object belongs to the topology
		self.delete()
			
	def getParent(self):
		return self.parent.upcast() if self.parent else None
			
	def getChildren(self):
		return [el.upcast() for el in self.children.all()]
			
	def getConnection(self):
		return self.connection.upcast() if self.connection else None
			
	def onChildAdded(self, child):
		pass
	
	def onChildRemoved(self, child):
		pass
			
	def getResource(self, type_):
		return resources.take(type_, self)
	
	def returnResource(self, type_, num):
		resources.give(type_, num, self)
		
	def getHostElements(self):
		mel = self.mainElement()
		return [mel] if mel else [] 
			
	def getHostConnections(self):
		return []
			
	def getConnectableElement(self):
		return None
		
	def getConnectedElement(self):
		if not self.connection:
			return None
		els = self.connection.getElements()
		assert len(els) == 2, "Connection %s has %d elements" % (self, len(els))
		if self.id == els[0].id:
			return els[1]
		if self.id == els[1].id:
			return els[0]
		assert False
		
	def getLocationData(self, maxDepth=3):
		"""
		Determines where this element is located and how much it wants other elements to be close by.
		Elements that are mainly connections other elements might overwrite this and use location
		data of these elements instead.
		Since this calculation can get stuck in a loop the depth is limited by a parameter. The
		maxDepth is decremented each time the calculation spans another element group.
		 
		@param maxDepth: Parameter limiting the maximal depth of calculation
		"""
		els = set()
		for el in self.getHostElements():
			els.add((el, self.SAME_HOST_AFFINITY, self.SAME_SITE_AFFINITY))
		return els
			
	def getLocationPrefs(self, children=True):
		"""
		Calculate and return host and site preferences by collecting and merging location data
		of connected elements 
		"""
		hostPrefs = {}
		sitePrefs = {}
		if self.connection:
			for el, sha, ssa in self.getConnectedElement().getLocationData():
				if not el.host:
					return #can this even happen?
				hostPrefs[el.host] = hostPrefs.get(el.host, 0.0) + sha + self.SAME_HOST_AFFINITY
				sitePrefs[el.host.site] = sitePrefs.get(el.host.site, 0.0) + ssa + self.SAME_SITE_AFFINITY
		if children:
			for ch in self.getChildren():
				hPref, sPref = ch.getLocationPrefs()
				for host, pref in hPref.iteritems():
					hostPrefs[host] = hostPrefs.get(host, 0.0) + pref 
				for site, pref in sPref.iteritems():
					sitePrefs[site] = sitePrefs.get(site, 0.0) + pref
		return (hostPrefs, sitePrefs)
			
	def triggerConnectionStart(self):
		con = self.getConnection()
		if con:
			con.triggerStart()
			
	def triggerConnectionStop(self):
		con = self.getConnection()
		if con:
			con.triggerStop()

	def onError(self, exc):
		pass
		
	@classmethod
	@cached(timeout=3600, maxSize=None)
	def getCapabilities(cls, host_):
		if not host_ and (cls.DIRECT_ACTIONS or cls.DIRECT_ATTRS):
			host_ = host.select(elementTypes=[cls.HOST_TYPE or cls.TYPE])
		if cls.DIRECT_ATTRS or cls.DIRECT_ACTIONS:
			host_cap = host_.getElementCapabilities(cls.HOST_TYPE or cls.TYPE)
		cap_actions = dict(cls.CUSTOM_ACTIONS)
		if cls.DIRECT_ACTIONS:
			for action, params in host_cap["actions"].iteritems():
				if not action in cls.DIRECT_ACTIONS_EXCLUDE:
					cap_actions[action] = params
		cap_attrs = {}
		for attr, params in cls.CUSTOM_ATTRS.iteritems():
			cap_attrs[attr] = params.info()
		if cls.DIRECT_ATTRS:
			for attr, params in host_cap["attrs"].iteritems():
				if not attr in cls.DIRECT_ATTRS_EXCLUDE:
					cap_attrs[attr] = params
		return {
			"attrs": cap_attrs,
			"actions": cap_actions,
			"children": cls.CAP_CHILDREN,
			"parent": cls.CAP_PARENT,
			"connectable": cls.CAP_CONNECTABLE
		}
			
	def info(self):
		if not (currentUser() is True or currentUser().hasFlag(Flags.Debug)):
			self.checkRole(Role.user)
		info = {
			"id": self.id,
			"type": self.type,
			"topology": self.topology.id,
			"parent": self.parent.id if self.hasParent() else None,
			"state": self.state,
			"attrs": self.attrs.copy(),
			"children": [ch.id for ch in self.getChildren()],
			"connection": self.connection.id if self.connection else None,
			"debug": {
					"host_elements": [(o.host.name, o.num) for o in self.getHostElements()],
					"host_connections": [(o.host.name, o.num) for o in self.getHostConnections()],
			}
		}
		mel = self.mainElement()
		if mel:
			info["attrs"].update(mel.attrs["attrs"])
		return info

	def fetchInfo(self):
		mel = self.mainElement()
		if mel:
			mel.updateInfo()

	def updateUsage(self):
		self.totalUsage.updateFrom([el.usageStatistics for el in self.getHostElements()]
								 + [con.usageStatistics for con in self.getHostConnections()])

	def __str__(self):
		return "%s_%d" % (self.type, self.id)
		

def get(id_, **kwargs):
	try:
		el = Element.objects.get(id=id_, **kwargs)
		return el.upcast()
	except Element.DoesNotExist:
		return None

def getAll(**kwargs):
	return (el.upcast() for el in Element.objects.filter(**kwargs))

def create(top, type_, parent=None, attrs={}):
	if parent:
		UserError.check(parent.topology == top, code=UserError.INVALID_CONFIGURATION,
			message="Parent must be from same topology")
	top.checkRole(Role.manager)	
	UserError.check(type_ in TYPES, code=UserError.UNSUPPORTED_TYPE, message="Unsupported type", data={"type": type_})
	el = TYPES[type_]()
	try:
		el.init(top, parent, attrs)
		el.save()
	except:
		el.remove()
		raise
	if parent:
		parent.onChildAdded(el)
	logging.logMessage("create", category="element", id=el.id)	
	logging.logMessage("info", category="element", id=el.id, info=el.info())		
	return el

from .. import currentUser, resources, host
		