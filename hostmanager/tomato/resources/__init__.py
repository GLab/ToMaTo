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
import random

from .. import config
from ..lib import db, attributes, logging #@UnresolvedImport
from ..lib.error import UserError, InternalError

TYPES = {}

def give(type_, num, owner):
	logging.logMessage("instance_return", category="resource", type=type_, num=num, owner=(owner.__class__.__name__.lower(), owner.id))
	if isinstance(owner, Element):
		instance = ResourceInstance.objects.get(type=type_, num=num, ownerElement=owner)
	elif isinstance(owner, Connection):
		instance = ResourceInstance.objects.get(type=type_, num=num, ownerConnection=owner)
	else:
		raise InternalError(code=InternalError.INVALID_PARAMETER,
			message="Owner must either be Element or Connection", data={"owner_type": owner.__class__.__name__})
	instance.delete()

def take(type_, owner, blacklist=None):
	if not blacklist: blacklist = []
	range_ = config.RESOURCES.get(type_)
	InternalError.check(range_, InternalError.CONFIGURATION_ERROR, "No resource entry found",
		data={"resource_type": type_})
	for try_ in xrange(0, 100): 
		num = random.choice(range_)
		if num in blacklist:
			continue
		try:
			ResourceInstance.objects.get(type=type_, num=num)
			continue
		except ResourceInstance.DoesNotExist:
			pass
		try:
			instance = ResourceInstance()
			instance.init(type_, num, owner)
			logging.logMessage("instance_take", category="resource", type=type_, num=num, owner=(owner.__class__.__name__.lower(), owner.id))
			return num
		except:
			pass
	raise InternalError(code=InternalError.RESOURCE_ERROR, message="Failed to obtain resource", data={"type": type_, "tries": try_})

from ..elements import Element
from ..connections import Connection

class Resource(db.ChangesetMixin, attributes.Mixin, models.Model):
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES]) #@ReservedAssignment
	attrs = db.JSONField()
	
	class Meta:
		pass

	def init(self, attrs=None):
		if not attrs: attrs = {}
		self.attrs = {}
		self.save()
		self.modify(attrs)
		
	def upcast(self):
		if not self.type in TYPES:
			return self
		try:
			return getattr(self, self.type)
		except:
			import traceback
			traceback.print_exc()
		raise InternalError(message="Failed to cast resource", code=InternalError.UPCAST, data={"id": self.id, "type": self.type})

	def modify(self, attrs):
		logging.logMessage("modify", category="resource", type=self.type, id=self.id, attrs=attrs)
		for key, value in attrs.iteritems():
			if hasattr(self, "modify_%s" % key):
				getattr(self, "modify_%s" % key)(value)
			else:
				self.attrs[key] = value
		logging.logMessage("info", category="resource", type=self.type, id=self.id, info=self.info())
		self.save()
	
	def remove(self):
		logging.logMessage("info", category="resource", type=self.type, id=self.id, info=self.info())
		logging.logMessage("remove", category="resource", type=self.type, id=self.id)
		self.delete()	
	
	def info(self):
		return {
			"id": self.id,
			"type": self.type,
			"attrs": self.attrs.copy(),
		}
	
class ResourceInstance(db.ChangesetMixin, attributes.Mixin, models.Model):
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES]) #@ReservedAssignment
	num = models.IntegerField()
	ownerElement = models.ForeignKey(Element, null=True)
	ownerConnection = models.ForeignKey(Connection, null=True)
	attrs = db.JSONField()
	
	class Meta:
		unique_together = (("num", "type"),)

	def init(self, type, num, owner, attrs=None): #@ReservedAssignment
		if not attrs: attrs = {}
		self.type = type
		self.num = num
		if isinstance(owner, Element):
			self.ownerElement = owner
		elif isinstance(owner, Connection):
			self.ownerConnection = owner
		else:
			raise InternalError(code=InternalError.INVALID_PARAMETER,
				message="Owner must either be Element or Connection", data={"owner_type": owner.__class__.__name__})
		self.attrs = attrs
		self.save()


def get(id_, **kwargs):
	try:
		el = Resource.objects.get(id=id_, **kwargs).upcast()
		if hasattr(el, "owner") and el.owner == currentUser():
			return el
		else:
			return None
	except:
		return None

def getAll(**kwargs):
	allRes = (res.upcast() for res in Resource.objects.filter(**kwargs))
	return (res for res in allRes if not hasattr(res, "owner") or res.owner == currentUser())

def create(type_, attrs=None):
	if not attrs: attrs = {}
	UserError.check(type_ in TYPES, UserError.UNSUPPORTED_TYPE, "Unknown resource type", data={"type": type_})
	res = TYPES[type_](owner=currentUser())
	res.init(attrs)
	res.save()
	logging.logMessage("create", category="resource", type=res.type, id=res.id, attrs=attrs)
	logging.logMessage("info", category="resource", type=res.type, id=res.id, info=res.info())
	return res

from .. import currentUser
