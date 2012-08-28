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