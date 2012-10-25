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

from ..connections import Connection
from ..accounting import UsageStatistics, Usage
from ..lib import db, attributes, util, logging #@UnresolvedImport
from ..lib.decorators import *
from .. import config

TYPES = {}
REMOVE_ACTION = "(remove)"

class Element(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES.keys()]) #@ReservedAssignment
	owner = models.CharField(max_length=20, validators=[db.nameValidator])
	parent = models.ForeignKey('self', null=True, related_name='children')
	connection = models.ForeignKey(Connection, null=True, related_name='elements')
	usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='element')
	state = models.CharField(max_length=20, validators=[db.nameValidator])
	attrs = db.JSONField()
	
	DOC = ""
	CAP_ACTIONS = {}
	CAP_NEXT_STATE = {}
	CAP_ATTRS = {}
	CAP_CHILDREN = {}
	CAP_PARENT = []
	CAP_CON_CONCEPTS = []
	DEFAULT_ATTRS = {}
	
	class Meta:
		pass

	def init(self, parent=None, attrs={}):
		if parent:
			fault.check(parent.type in self.CAP_PARENT, "Parent type %s not allowed for type %s", (parent.type, self.type))
			fault.check(self.type in parent.CAP_CHILDREN, "Parent type %s does not allow children of type %s", (parent.type, self.type))
			fault.check(parent.state in parent.CAP_CHILDREN[self.type], "Parent type %s does not allow children of type %s in state %s", (parent.type, self.type, parent.state))
		else:
			fault.check(None in self.CAP_PARENT, "Type %s needs parent", self.type)
		self.parent = parent
		self.owner = currentUser()
		self.attrs = dict(self.DEFAULT_ATTRS)
		self.save()
		stats = UsageStatistics()
		stats.init()
		stats.save()
		self.usageStatistics = stats
		if not os.path.exists(self.dataPath()):
			os.makedirs(self.dataPath())
		self.modify(attrs)

	def _saveAttributes(self):
		pass #disable automatic attribute saving

	def isBusy(self):
		return hasattr(self, "_busy") and self._busy
	
	def setBusy(self, busy):
		self._busy = busy
		
	def dataPath(self, filename=""):
		"""
		This method can be used to create filenames relative to a directory
		that is specific for this object. The base directory is created when 
		this object is initialized and recursively removed when the object is
		removed.
		
		All custom files should use paths relative to the base directory.
		Note: If filename contains folder names the using class must take care
			that they exist.
		
		@param filename: a filename relative to the data path
		@type filename: str
		"""
		return os.path.join(config.DATA_DIR, self.TYPE, str(self.id), filename)		
		
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

	def checkModify(self, attrs):
		"""
		Checks whether the attribute change can succeed before changing the
		attributes.
		If checks whether the attributes are listen in CAP_ATTRS and if the
		current object state is listed in CAP_ATTRS[NAME].
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""
		fault.check(not self.isBusy(), "Object is busy", code=fault.OBJECT_BUSY)
		for key in attrs.keys():
			fault.check(key in self.CAP_ATTRS, "Unsuported attribute for %s: %s", (self.type, key), code=fault.UNSUPPORTED_ATTRIBUTE)
			self.CAP_ATTRS[key].check(self, attrs[key])
		
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
			for key, value in attrs.iteritems():
				getattr(self, "modify_%s" % key)(value)
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
		fault.check(not self.isBusy(), "Object is busy", code=fault.OBJECT_BUSY)
		fault.check(action in self.CAP_ACTIONS, "Unsuported action for %s: %s", (self.type, action), code=fault.UNSUPPORTED_ACTION)
		fault.check(self.state in self.CAP_ACTIONS[action], "Action %s of %s can not be executed in state %s", (action, self.type, self.state), code=fault.INVALID_STATE)
	
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
			res = getattr(self, "action_%s" % action)(**params)
		finally:
			self.setBusy(False)
		self.save()
		if action in self.CAP_NEXT_STATE:
			fault.check(self.state == self.CAP_NEXT_STATE[action], "Action %s of %s lead to wrong state, should be %s, was %s", (action, self.type, self.CAP_NEXT_STATE[action], self.state), fault.INTERNAL_ERROR)
		logging.logMessage("action end", category="element", id=self.id, action=action, params=params, res=res)
		logging.logMessage("info", category="element", id=self.id, info=self.info())			
		return res

	def checkRemove(self, recurse=True):
		fault.check(not self.isBusy(), "Object is busy", code=fault.OBJECT_BUSY)
		fault.check(recurse or self.children.empty(), "Cannot remove element with children")
		fault.check(not REMOVE_ACTION in self.CAP_ACTIONS or self.state in self.CAP_ACTIONS[REMOVE_ACTION], "Element type %s can not be removed in its state %s", (self.type, self.state), code=fault.INVALID_STATE)
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
		logging.logMessage("info", category="element", id=self.id, info=self.info())
		logging.logMessage("remove", category="element", id=self.id)
		if self.parent:
			self.getParent().onChildRemoved(self)
		for ch in self.getChildren():
			ch.remove(recurse=True)
		if self.connection:
			self.getConnection().remove()
		self.delete()
		if os.path.exists(self.dataPath()):
			shutil.rmtree(self.dataPath())
			
	def getParent(self):
		return self.parent.upcast() if self.parent else None
			
	def getChildren(self):
		return [el.upcast() for el in self.children.all()]
			
	def getConnection(self):
		return self.connection.upcast() if self.connection else None
		
	def onConnected(self):
		pass
	
	def onDisconnected(self):
		pass
			
	def onChildAdded(self, child):
		pass
	
	def onChildRemoved(self, child):
		pass
			
	def getResource(self, type_):
		return resources.take(type_, self)
	
	def returnResource(self, type_, num):
		resources.give(type_, num, self)
		
	@classmethod	
	def cap_attrs(cls):
		return dict([(key, value.info()) for (key, value) in cls.CAP_ATTRS.iteritems()])
					
	def info(self):
		return {
			"id": self.id,
			"type": self.type,
			"parent": self.parent.id if self.hasParent() else None,
			"state": self.state,
			"attrs": self.attrs.copy(),
			"children": [ch.id for ch in self.getChildren()],
			"connection": self.connection.id if self.connection else None,
		}
		
	def updateUsage(self, usage, data):
		pass

def get(id_, **kwargs):
	try:
		el = Element.objects.get(id=id_, **kwargs)
		return el.upcast()
	except Element.DoesNotExist:
		return None

def getAll(**kwargs):
	return (el.upcast() for el in Element.objects.filter(**kwargs))

def create(type_, parent=None, attrs={}):
	fault.check(type_ in TYPES, "Unsupported type: %s", type_)
	fault.check(not parent or parent.owner == currentUser(), "Parent element belongs to different user")
	el = TYPES[type_]()
	el.init(parent, attrs)
	el.save()
	if parent:
		parent.onChildAdded(el)
	logging.logMessage("create", category="element", id=el.id)	
	logging.logMessage("info", category="element", id=el.id, info=el.info())	
	return el

from .. import fault, currentUser, resources
		