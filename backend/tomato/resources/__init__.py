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
import sys

from ..lib import db, attributes #@UnresolvedImport
from ..lib.error import UserError, InternalError

TYPES = {}

class Resource(db.ChangesetMixin, attributes.Mixin, models.Model):
	type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES]) #@ReservedAssignment
	attrs = db.JSONField()
	
	FIELD_NAME = None #take type as field name
	
	class Meta:
		pass

	def init(self, attrs={}):
		self.attrs = {}
		self.save()
		try:
			self.modify(attrs)
		except Exception, e:
			try:
				self.remove()
			except:
				pass
			raise e
		
	def upcast(self):
		if not self.type in TYPES:
			return self
		try:
			field = TYPES[self.type].FIELD_NAME or self.type
			return getattr(self, field)
		except:
			import traceback
			traceback.print_exc()
		id, type = self.id, self.type
		self.remove()
		raise InternalError(code=InternalError.UPCAST, message="Failed to cast resource to its type",
			  data={"id": id, "type": type})
	
	def modify(self, attrs):
		if not _initPhase:
			UserError.check(currentUser().hasFlag(Flags.GlobalHostManager) or currentUser().hasFlag(Flags.GlobalAdmin),
				code=UserError.DENIED, message="Method only allowed for admin users")
		for key, value in attrs.iteritems():
			if hasattr(self, "modify_%s" % key):
				getattr(self, "modify_%s" % key)(value)
			else:
				self.attrs[key] = value
		self.save()
	
	def remove(self):
		UserError.check(currentUser().hasFlag(Flags.GlobalHostManager) or currentUser().hasFlag(Flags.GlobalAdmin),
			code=UserError.DENIED, message="Method only allowed for admin users")
		self.delete()
	
	def info(self):
		return {
			"id": self.id,
			"type": self.type,
			"attrs": self.attrs.copy(),
		}
	
def get(id_, **kwargs):
	try:
		el = Resource.objects.get(id=id_, **kwargs)
		return el.upcast()
	except:
		return None

def getByType(type_, **kwargs):
	try:
		el = Resource.objects.get(type=type_, **kwargs)
		return el.upcast()
	except:
		return None

def getAll(**kwargs):
	return (res.upcast() for res in Resource.objects.filter(**kwargs))

def create(type_, attrs=None):
	if not attrs: attrs = {}
	if not _initPhase:
		UserError.check(currentUser().hasFlag(Flags.GlobalHostManager) or currentUser().hasFlag(Flags.GlobalAdmin),
			code=UserError.DENIED, message="Method only allowed for admin users")
	if type_ in TYPES:
		res = TYPES[type_]()
	else:
		res = Resource(type=type_)
	try:
		res.init(attrs)
		res.save()
	except Exception, e:
		if res.id:
			try:
				res.remove()
			except:
				pass
		raise e
	return res

def init():
	import profile
	global _initPhase
	_initPhase = True
	for tech in profile.TECHS:
		try:
			profile.getPreferred(tech)
		except:
			print >>sys.stderr, "Adding default profile for %s" % tech
			attrs = {"tech": tech, "name": "normal", "label": "Normal", "preference": 10}
			attrs.update(profile.DEFAULTS[tech])
			create("profile", attrs)
	_initPhase = False

_initPhase=False

from .. import currentUser
from ..auth import Flags