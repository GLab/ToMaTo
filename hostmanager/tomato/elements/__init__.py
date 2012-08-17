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

from tomato.lib import db, attributes, util
from tomato.lib.decorators import *
from tomato import config

# Socat:
#socat tun:127.0.0.1/32,tun-type=tap,iff-up,tun-name=IFNAME udp-listen:PORT
#socat tun:127.0.0.1/32,tun-type=tap,iff-up,tun-name=IFNAME udp-connect:IP:PORT


TYPES = {}
REMOVE_ACTION = "__remove__"

class Element(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES.keys()])
	owner = models.CharField(max_length=20, validators=[db.nameValidator])
	parent = models.ForeignKey('self', null=True, related_name='children')
	connection = models.ForeignKey(Connection, null=True, related_name='elements')
	state = models.CharField(max_length=20, validators=[db.nameValidator])
	attrs = db.JSONField()
	
	CAP_ACTIONS = {}
	CAP_NEXT_STATE = {}
	CAP_ATTRS = {}
	CAP_CHILDREN = {}
	CAP_PARENT = []
	CAP_CON_PARADIGMS = []
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
		if not os.path.exists(self.dataPath()):
			os.makedirs(self.dataPath())
		self.modify(attrs)

	def dataPath(self, filename=""):
		return os.path.join(config.DATA_DIR, self.TYPE, str(self.id), filename)		
		
	def upcast(self):
		try:
			return getattr(self, self.type)
		except:
			pass
		fault.raise_("Failed to cast element #%d to type %s" % (self.id, self.type), code=fault.INTERNAL_ERROR)

	def hasParent(self):
		return not self.parent is None

	def checkModify(self, attrs):
		for key in attrs.keys():
			fault.check(key in self.CAP_ATTRS, "Unsuported attribute for %s: %s", (self.type, key))
			fault.check(self.state in self.CAP_ATTRS[key], "Attribute %s of %s can not be changed in state %s", (key, self.type, self.state))
		
	def modify(self, attrs):
		self.checkModify(attrs)
		for key, value in attrs.iteritems():
			getattr(self, "modify_%s" % key)(value)
		self.save()
	
	def checkAction(self, action):
		fault.check(action in self.CAP_ACTIONS, "Unsuported action for %s: %s", (self.type, action))
		fault.check(self.state in self.CAP_ACTIONS[action], "Action %s of %s can not be executed in state %s", (action, self.type, self.state))
	
	def action(self, action, params):
		self.checkAction(action)
		getattr(self, "action_%s" % action)(**params)
		self.save()
		if action in self.CAP_NEXT_STATE:
			fault.check(self.state == self.CAP_NEXT_STATE[action], "Action %s of %s lead to wrong state, should be %s, was %s", (action, self.type, self.CAP_NEXT_STATE[action], self.state), fault.INTERNAL_ERROR)

	def checkRemove(self, recurse=True):
		fault.check(recurse or self.children.empty(), "Cannot remove element with children")
		fault.check(not REMOVE_ACTION in self.CAP_ACTIONS or self.state in self.CAP_ACTIONS[REMOVE_ACTION], "Element type %s can not be removed in its state %s", (self.type, self.state))
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
			
	def info(self):
		return {
			"id": self.id,
			"type": self.type,
			"parent_id": self.parent.id if self.hasParent() else None,
			"state": self.state,
			"attrs": self.attrs,
			"children": [ch.id for ch in self.getChildren()],
			"connection": self.connection.id if self.connection else None,
		}
		
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
	el = TYPES[type_]()
	el.init(parent, attrs)
	el.save()
	if parent:
		parent.onChildAdded(el)
	return el

from tomato import fault, currentUser, resources
		