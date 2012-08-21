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

from tomato.accounting import UsageStatistics
from tomato.lib import db, attributes, util
from tomato.lib.decorators import *

TYPES = {}
REMOVE_ACTION = "__remove__"

"""
General interface:
- The element must provide two methods:
	onConnected()
  		Called when both elements are successfully connected and communication
  		is now possible.
  	onDisconnected()
  		Called when one element was disconnected and communication is no longer
  		possible.
"""


CONCEPT_INTERFACE = "interface"
"""
Interface concept interface:
- The connection must provide two methods:
	connectInterface(ifname)
		Called to connect the interface ifname to the connection.
		The interface must exist and be fully configured.
	disconnectInterface(ifname)
		Called to disconnect the interface ifname from the connection.
		The interface must exist all the time until this call.
- The element must provide the following methods:
	interfaceName()
		This method must return the interface name if the interface exists
		and is ready for connection or None if not.
"""

CONCEPT_BRIDGE = "bridge"
"""
Bridge concept interface:
- The connection must provide two methods:
	connectBridge(bridgename)
		Called to connect the bridge bridgename to the connection.
		The bridge must exist and be fully configured.
	disconnectBridge(bridgename)
		Called to disconnect the bridge bridgename from the connection.
		The bridge must exist all the time until this call.
- The element must provide the following methods:
	bridgeName()
		This method must return the bridge name if the bridge exists and is
		ready for connection or None if not.
"""


class Connection(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES.keys()]) #@ReservedAssignment
	owner = models.CharField(max_length=20, validators=[db.nameValidator])
	state = models.CharField(max_length=20, validators=[db.nameValidator])
	usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='connection')
	attrs = db.JSONField()
	#elements: set of elements.Element
	
	CAP_ACTIONS = {}
	CAP_ATTRS = {}
	CAP_CON_CONCEPTS = []
	DEFAULT_ATTRS = {}
	
	class Meta:
		pass

	def init(self, el1, el2, attrs={}):
		concept_ = self.determineConcept(el1, el2)
		fault.check(concept_, "No connection concept found to connect elements of type %s and %s with connection of type %s", (el1.type, el2.type, self.type))
		self.owner = currentUser()
		self.attrs = dict(self.DEFAULT_ATTRS)
		self.save()
		self.elements.add(el1)
		self.elements.add(el2)
		self.save()
		stats = UsageStatistics()
		stats.init()
		stats.save()
		self.usageStatistics = stats		
		if not os.path.exists(self.dataPath()):
			os.makedirs(self.dataPath())
		self.modify(attrs)
		
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
		fault.raise_("Failed to cast connection #%d to type %s" % (self.id, self.type), code=fault.INTERNAL_ERROR)

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

	@classmethod
	def determineConcept(cls, el1, el2):
		for (p1, p2) in cls.CAP_CON_CONCEPTS:
			if p1 in el1.CAP_CON_CONCEPTS and p2 in el2.CAP_CON_CONCEPTS:
				return (p1, p2)
			if p2 in el1.CAP_CON_CONCEPTS and p1 in el2.CAP_CON_CONCEPTS:
				return (p2, p1)
		return None

	def checkModify(self, attrs):
		"""
		Checks whether the attribute change can succeed before changing the
		attributes.
		If checks whether the attributes are listen in CAP_ATTRS and if the
		current object state is listed in CAP_ATTRS[NAME].
		
		@param attrs: Attributes to change
		@type attrs: dict
		"""
		for key in attrs.keys():
			fault.check(key in self.CAP_ATTRS, "Unsuported attribute for %s: %s", (self.type, key))
			fault.check(self.state in self.CAP_ATTRS[key], "Attribute %s of %s can not be changed in state %s", (key, self.type, self.state))
		
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
		for key, value in attrs.iteritems():
			getattr(self, "modify_%s" % key)(value)
		self.save()
	
	def checkAction(self, action):
		"""
		Checks if the action can be executed. This method checks if the action
		is listed in CAP_ACTIONS and if the current state is listed in 
		CAP_ACTIONS[action].
		
		@param action: Action to check
		@type action: str
		"""
		fault.check(action in self.CAP_ACTIONS, "Unsuported action for %s: %s", (self.type, action))
		fault.check(self.state in self.CAP_ACTIONS[action], "Action %s of %s can not be executed in state %s", (action, self.type, self.state))
	
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
		getattr(self, "action_%s" % action)(**params)
		self.save()

	def setState(self, state, dummy=None):
		self.state = state
		self.save()

	def checkRemove(self):
		fault.check(not REMOVE_ACTION in self.CAP_ACTIONS or self.state in self.CAP_ACTIONS[REMOVE_ACTION], "Connector type %s can not be removed in its state %s", (self.type, self.state))

	def remove(self):
		self.checkRemove()
		self.elements.clear() #Important, otherwise elements will be deleted
		self.delete()
		if os.path.exists(self.dataPath()):
			shutil.rmtree(self.dataPath())
			
	def getElements(self):
		return [el.upcast() for el in self.elements.all()]
			
	def info(self):
		return {
			"id": self.id,
			"type": self.type,
			"state": self.state,
			"attrs": self.attrs,
			"elements": [el.id for el in self.getElements()],
		}
		
	def getResource(self, type_):
		from tomato import resources #needed to break import cycle
		return resources.take(type_, self)
	
	def returnResource(self, type_, num):
		from tomato import resources #needed to break import cycle
		resources.give(type_, num, self)
		
	def updateUsage(self, usage, data):
		pass

		
def get(id_, **kwargs):
	try:
		con = Connection.objects.get(id=id_, **kwargs)
		return con.upcast()
	except Connection.DoesNotExist:
		return None

def getAll(**kwargs):
	return (con.upcast() for con in Connection.objects.filter(**kwargs))

def create(el1, el2, type_=None, attrs={}):
	if type_:
		fault.check(type_ in TYPES, "Unsupported type: %s", type_)
		fault.check(not el1.connection, "Element #%d is already connected", el1.id)
		fault.check(not el2.connection, "Element #%d is already connected", el2.id)
		con = TYPES[type_]()
		con.init(el1, el2, attrs)
		con.save()
		return con
	else:
		for type_ in TYPES:
			if TYPES[type_].determineConcept(el1, el2):
				return create(el1, el2, type_, attrs)
		fault.check(False, "Failed to find matching connection type for element types %s and %s", (el1.type, el2.type))

from tomato import fault, currentUser, config
