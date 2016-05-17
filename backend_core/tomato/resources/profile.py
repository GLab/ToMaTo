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

from ..generic import *
from ..db import *
from ..lib.error import UserError, InternalError
from ..lib.exceptionhandling import wrap_errors

TECHS = ["kvmqm", "openvz", "repy"]
DEFAULTS = {
	"kvmqm": {"ram": 512, "cpus": 1, "diskspace": 10240},
	"openvz": {"ram": 512, "cpus": 1, "diskspace": 10240},
	"repy": {"ram": 50, "cpus": 0.25},
}

class Profile(Entity, BaseDocument):
	tech = StringField(required=True)
	name = StringField(required=True, unique_with='tech')
	preference = IntField(default=0, required=True)
	label = StringField()
	description = StringField()
	restricted = BooleanField(default=False)
	ram = IntField(min_value=0)
	cpus = FloatField(min_value=0)
	diskspace = IntField(min_value=0)
	meta = {
		'ordering': ['tech', '+preference', 'name'],
		'indexes': [
			('tech', 'preference'), ('tech', 'name')
		]
	}

	def remove(self):
		if self.id:
			self.delete()

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=remove)
	}
	ATTRIBUTES = {
		"id": IdAttribute(),
		"name": Attribute(field=name, schema=schema.Identifier()),
		"tech": Attribute(field=tech, schema=schema.String(options=TECHS)),
		"preference": Attribute(field=preference, schema=schema.Int(minValue=0)),
		"label": Attribute(field=label, schema=schema.String()),
		"description": Attribute(field=description, schema=schema.String()),
		"restricted": Attribute(field=restricted, schema=schema.Bool()),
		"ram": Attribute(field=ram, schema=schema.Int(minValue=0)),
		"cpus": Attribute(field=cpus, schema=schema.Number(minValue=0)),
		"diskspace": Attribute(field=diskspace, schema=schema.Int(minValue=0))
	}

	def init(self, attrs):
		for attr in ["name", "tech"]:
			UserError.check(attr in attrs, code=UserError.INVALID_CONFIGURATION, message="Profile needs attribute",
				data={"attribute": attr})
		Entity.init(self, attrs)

	@classmethod
	def get(cls, tech, name):
		try:
			return Profile.objects.get(tech=tech, name=name)
		except:
			return None

	@classmethod
	def getPreferred(cls, tech):
		prfls = Profile.objects.filter(tech=tech).order_by("-preference")
		InternalError.check(prfls, code=InternalError.CONFIGURATION_ERROR, message="No profile for this type registered", data={"tech": tech})
		return prfls[0]

	@classmethod
	def create(cls, attrs):
		prfls = Profile.objects.filter(name=attrs["name"], tech=attrs["tech"])
		UserError.check(not prfls, code=UserError.ALREADY_EXISTS,
						message="There exists already a profile for this technology with a similar name",
						data={"name":attrs["name"],"tech":attrs["tech"]})
		obj = cls()
		obj.init(attrs)
		obj.save()
		return obj