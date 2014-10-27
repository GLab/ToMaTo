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

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^tomato\.lib\.db\.JSONField"])

import re
from .error import UserError

class Attr:
	def __init__(self, name, desc="", unit=None, states=None, default=None, null=False, type=None, options=None, regExp=None, minValue=None, maxValue=None):
		self.name = name
		self.desc = desc
		self.states = states
		self.default = default
		self.null = null
		self.type = type
		self.options = options
		self.unit = unit
		self.regExp = regExp
		self.minValue = minValue
		self.maxValue = maxValue
	def check(self, obj, value):
		if self.states and not obj.state in self.states:
			raise UserError(code=UserError.INVALID_STATE, message="Invalid state for attribute",
				data={"attribute": self.name, "state": obj.state, "allowed_states": self.states})
		self.conv(value)
	def conv(self, value):
		if value is None:
			if not self.null:
				raise UserError(code=UserError.INVALID_VALUE, message="Invalid value, must not be null",
					data={"attribute": self.name, "value": value})
			return None
		try:
			if self.type == "int":
				value = int(value)
			if self.type == "float":
				value = float(value)
			if self.type == "str":
				value = unicode(value)
			if self.type == "bool":
				value = bool(value)
		except:
			raise UserError(code=UserError.INVALID_VALUE, message="Invalid value, failed to convert",
				data={"attribute": self.name, "value": value, "type": self.type})
		if self.options and not value in self.options.keys():
			raise UserError(code=UserError.INVALID_VALUE, message="Invalid value, must choose from list",
				data={"attribute": self.name, "value": value, "options": self.options.keys()})
		if not self.minValue is None and value < self.minValue:
			raise UserError(code=UserError.INVALID_VALUE, message="Invalid value, below minimum",
				data={"attribute": self.name, "value": value, "minimum": self.minValue})
		if not self.maxValue is None and value > self.maxValue:
			raise UserError(code=UserError.INVALID_VALUE, message="Invalid value, above maximum",
				data={"attribute": self.name, "value": value, "maximum": self.maxValue})
		if self.regExp and not re.match(self.regExp, value):
			raise UserError(code=UserError.INVALID_VALUE, message="Invalid value, must match pattern",
				data={"attribute": self.name, "value": value, "pattern": self.regExp})
		return value
	def set(self, obj, value):
		value = self.conv(value)
		if self.states and not obj.state in self.states:
			raise UserError(code=UserError.INVALID_STATE, message="Invalid state for attribute",
				data={"attribute": self.name, "state": obj.state, "allowed_states": self.states})
		obj.setAttribute(self.name, value)
	def get(self, obj):
		return obj.getAttribute(self.name, self.default)
	def delete(self, obj):
		obj.deleteAttribute(self.name)
	def attribute(self):
		return property ( lambda obj: self.get(obj), lambda obj, val: self.set(obj, val), lambda obj: self.delete(obj) )
	def info(self):
		d = {}
		for name in ["name", "unit", "states", "default", "null", "desc", "type", "options", "regExp", "minValue", "maxValue"]:
			value = getattr(self, name)
			name = name.lower()
			if not value is None:
				d[name] = value
		return d

def between(min, max, faultType=Exception, faultStr="Value must be between %(min)s and %(max)s but was %(value)s"): #@ReservedAssignment
	def validate(val):
		if min <= val <= max:
			return val
		else:
			raise faultType(faultStr % {"min": min, "max": max, "value": val})
	return validate

def oneOf(options, faultType=Exception, faultStr="Value must be one of %(options)s but was %(value)s"):
	def validate(val):
		if val in options:
			return val
		else:
			raise faultType(faultStr % {"options": options, "value": val})
	return validate

def attribute(name, type_=lambda x: x, default=None, null=True):
	return property ( lambda self_: self_.getAttribute(name, default),
				      lambda self_,value: self_.setAttribute(name, value if (value is None and null) else type_(value)),
				      lambda self_:self_.deleteAttribute(name) ) 

class Mixin:
	def _saveAttributes(self):
		self.save()
	def hasAttribute(self, name):
		assert isinstance(self.attrs, dict)
		return name in self.attrs
	def getAttribute(self, name, default=None):
		assert isinstance(self.attrs, dict), type(self.attrs)
		try:
			return self.attrs[name]
		except:
			return default
	def getAttributes(self):
		assert isinstance(self.attrs, dict)
		return self.attrs.copy()
	def setAttribute(self, name, value):
		assert isinstance(self.attrs, dict)
		self.attrs[name] = value
		self._saveAttributes()
	def setAttributes(self, attrs):
		assert isinstance(self.attrs, dict)
		self.attrs.update(attrs)
		self._saveAttributes()
	def deleteAttribute(self, name):
		assert isinstance(self.attrs, dict)
		try:
			del self.attrs[name]
			self._saveAttributes()
		except KeyError:
			pass
	def clearAttributes(self):
		self.attrs = {}
		self._saveAttributes()
	def setPrivateAttributes(self, attrs):
		assert isinstance(self.attrs, dict)
		for k, v in attrs.iteritems():
			if k.startswith("_"):
				self.attrs[k] = v
		self._saveAttributes()
	def getPrivateAttributes(self):
		assert isinstance(self.attrs, dict)
		data = {}
		for k, v in self.attrs.iteritems():
			if k.startswith("_"):		
				data[k] = v
		return data