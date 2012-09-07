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

import os, shutil
from django.db import models

from tomato.connections import Connection
from tomato.auth import Flags
from tomato.auth.permissions import Permissions, PermissionMixin, Role
from tomato.topology import Topology
from tomato.lib import db, attributes, util, logging #@UnresolvedImport
from tomato.accounting import UsageStatistics
from tomato.lib.decorators import *
from tomato import config

TYPES = {}
REMOVE_ACTION = "(remove)"

class Element(PermissionMixin, db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
	topology = models.ForeignKey(Topology, null=False, related_name="elements")
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES.keys()]) #@ReservedAssignment
	state = models.CharField(max_length=20, validators=[db.nameValidator])
	parent = models.ForeignKey('self', null=True, related_name='children')
	connection = models.ForeignKey(Connection, null=True, related_name='elements')
	permissions = models.ForeignKey(Permissions, null=False)
	totalUsage = models.OneToOneField(UsageStatistics, null=True, related_name='+')
	attrs = db.JSONField()
	
	DIRECT_ACTIONS = True
	DIRECT_ACTIONS_EXCLUDE = []
	CUSTOM_ACTIONS = {}
	
	DIRECT_ATTRS = True
	DIRECT_ATTRS_EXCLUDE = []
	CUSTOM_ATTRS = {}
	
	DOC = ""
	CAP_CHILDREN = {}
	CAP_PARENT = []
	CAP_CONNECTABLE = False
	DEFAULT_ATTRS = {}
	
	class Meta:
		pass

	def init(self, topology, parent=None, attrs={}):
		topology.checkRole(Role.manager)
		if parent:
			fault.check(parent.type in self.CAP_PARENT, "Parent type %s not allowed for type %s", (parent.type, self.type))
			fault.check(self.type in parent.CAP_CHILDREN, "Parent type %s does not allow children of type %s", (parent.type, self.type))
			fault.check(parent.state in parent.CAP_CHILDREN[self.type], "Parent type %s does not allow children of type %s in state %s", (parent.type, self.type, parent.state))
		else:
			fault.check(None in self.CAP_PARENT, "Type %s needs parent", self.type)
		self.topology = topology
		self.permissions = topology.permissions
		self.parent = parent
		self.attrs = dict(self.DEFAULT_ATTRS)
		self.totalUsage = UsageStatistics.objects.create()
		self.save()
		self.modify(attrs)

	def _saveAttributes(self):
		pass #disable automatic attribute saving

	def isBusy(self):
		return hasattr(self, "_busy") and self._busy
	
	def setBusy(self, busy):
		self._busy = busy
		
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
			return getattr(self, self.type)
		except:
			pass
		fault.raise_("Failed to cast element #%d to type %s" % (self.id, self.type), code=fault.INTERNAL_ERROR)

	def hasParent(self):
		return not self.parent is None

	def mainElement(self):
		return None

	def remoteType(self):
		return self.type

	def _remoteAttrs(self):
		caps = host.getElementCapabilities(self.remoteType())
		allowed = caps["attrs"].keys() if caps else []
		attrs = {}
		for key, value in self.attrs.iteritems():
			if key in allowed:
				attrs[key] = value
		return attrs

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
		fault.check(not self.isBusy(), "Object is busy")
		mel = self.mainElement()
		direct = []
		if self.DIRECT_ATTRS:
			if mel:
				direct = mel.getAllowedAttributes()
			else:
				caps = host.getElementCapabilities(self.remoteType())
				direct = caps["attrs"].keys() if caps else []
		for key in attrs.keys():
			if key in direct and not key in self.DIRECT_ATTRS_EXCLUDE:
				continue
			fault.check(key in self.CUSTOM_ATTRS, "Unsuported attribute for %s: %s", (self.type, key))
			fault.check(self.state in self.CUSTOM_ATTRS[key], "Attribute %s of %s can not be changed in state %s", (key, self.type, self.state))
		
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
		self.checkModify(attrs)
		logging.logMessage("modify", category="element", id=self.id, attrs=attrs)
		self.setBusy(True)
		try:
			directAttrs = {}
			for key, value in attrs.iteritems():
				if key in self.CUSTOM_ATTRS:
					getattr(self, "modify_%s" % key)(value)
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
		finally:
			self.setBusy(False)
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
			fault.check(not currentUser().hasFlag(Flags.OverQuota), "Over quota")
		fault.check(not self.isBusy(), "Object is busy")
		if self.DIRECT_ACTIONS and not action in self.DIRECT_ACTIONS_EXCLUDE:
			mel = self.mainElement()
			if mel and action in mel.getAllowedActions():
				return
		fault.check(action in self.CUSTOM_ACTIONS, "Unsuported action for %s: %s", (self.type, action))
		fault.check(self.state in self.CUSTOM_ACTIONS[action], "Action %s of %s can not be executed in state %s", (action, self.type, self.state))
	
	def action(self, action, params):
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
		self.checkAction(action)
		logging.logMessage("action start", category="element", id=self.id, action=action, params=params)
		self.setBusy(True)
		try:
			if action in self.CUSTOM_ACTIONS:
				res = getattr(self, "action_%s" % action)(**params)
			else:
				mel = self.mainElement()
				assert mel
				if hasattr(self, "before_%s" % action):
					getattr(self, "before_%s" % action)(**params)
				res = mel.action(action, params)
				self.setState(mel.state, True)
				if hasattr(self, "after_%s" % action):
					getattr(self, "after_%s" % action)(**params)
		except Exception, exc:
			self.onError(exc)
			raise
		finally:
			self.setBusy(False)
		self.save()
		logging.logMessage("action end", category="element", id=self.id, action=action, params=params, result=res)
		logging.logMessage("info", category="element", id=self.id, info=self.info())					
		return res

	def checkRemove(self, recurse=True):
		fault.check(not self.isBusy(), "Object is busy")
		self.checkRole(Role.manager)
		fault.check(recurse or self.children.empty(), "Cannot remove element with children")
		fault.check(not REMOVE_ACTION in self.CUSTOM_ACTIONS or self.state in self.CUSTOM_ACTIONS[REMOVE_ACTION], "Element type %s can not be removed in its state %s", (self.type, self.state))
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
		self.checkRemove(recurse)
		logging.logMessage("info", category="topology", id=self.id, info=self.info())
		logging.logMessage("remove", category="topology", id=self.id)
		if self.parent:
			self.getParent().onChildRemoved(self)
		for ch in self.getChildren():
			ch.remove(recurse=True)
		if self.connection:
			self.getConnection().remove()
		self.totalUsage.delete()
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
			
	def info(self):
		if not currentUser().hasFlag(Flags.Debug):
			self.checkRole(Role.user)
		info = {
			"id": self.id,
			"type": self.type,
			"topology": self.topology.id,
			"parent": self.parent.id if self.hasParent() else None,
			"state": self.state,
			"attrs": self.attrs,
			"children": [ch.id for ch in self.getChildren()],
			"connection": self.connection.id if self.connection else None,
		}
		mel = self.mainElement()
		if mel:
			info["attrs"].update(mel.attrs["attrs"])
		return info

	def updateUsage(self, now):
		self.totalUsage.updateFrom(now, [el.usageStatistics for el in self.getHostElements()]
								 + [con.usageStatistics for con in self.getHostConnections()])

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
		fault.check(parent.topology == top, "Parent must be from same topology")
	top.topology.checkRole(Role.manager)	
	fault.check(type_ in TYPES, "Unsupported type: %s", type_)
	el = TYPES[type_]()
	el.init(top, parent, attrs)
	el.save()
	if parent:
		parent.onChildAdded(el)
	logging.logMessage("create", category="element", id=el.id)	
	logging.logMessage("info", category="element", id=el.id, info=el.info())		
	return el

from tomato import fault, currentUser, resources, host
		