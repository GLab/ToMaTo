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

import json
import datetime
from django.db import models, transaction
from django.core import validators
from .. import config

"""
A :class:`TextField` that stores serialized data in the form of JSON.  You can
set th"is field to be any Python data structure that contains data that can be
serialized by the ``simplejson`` serializer, in addition to DateTime objects,
which can be serialized even though upon deserialization they will remain
strings.
"""

class JSONDateEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, basestring):
			return obj
		elif isinstance(obj, datetime.datetime):
			return obj.strftime('%Y-%m-%d %H:%M:%S')
		elif isinstance(obj, datetime.date):
			return obj.strftime('%Y-%m-%d')
		elif isinstance(obj, datetime.time):
			return obj.strftime('%H:%M:%S')
		return json.JSONEncoder.default(self, obj)

class JSONField(models.TextField):
	description = "Data that serializes and deserializes into and out of JSON."

	# Used so to_python() is called
	__metaclass__ = models.SubfieldBase

	def _dumps(self, data):
		return JSONDateEncoder().encode(data)

	def _loads(self, str_):
		if config.MAINTENANCE:
			return str_
		return json.loads(str_, encoding="UTF-8")

	def db_type(self):
		return 'text'

	def to_python(self, value):
		"""Convert our string value to JSON after we load it from the DB"""
		if value == "":
			return {}
		try:
			if isinstance(value, basestring):
				return self._loads(value)
		except ValueError:
			print value
			import traceback
			traceback.print_exc()
			pass
		return value

	def get_db_prep_save(self, value, *args, **kwargs):
		"""Convert our JSON object to a string before we save"""
		if value == "":
			return None
		if isinstance(value, dict):
			value = self._dumps(value)
		return super(JSONField, self).get_db_prep_save(value, *args, **kwargs)
	
class CommaSeparatedListField(models.TextField):
	description = "A list of simple strings"

	# Used so to_python() is called
	__metaclass__ = models.SubfieldBase

	def db_type(self):
		return 'text'

	def to_python(self, value):
		if not value:
			return []
		return value.split(",")[1:-1]

	def get_db_prep_save(self, value):
		if not value:
			return ""
		if isinstance(value, list):
			value = "," + (",".join(value)) + ","
		return super(CommaSeparatedListField, self).get_db_prep_save(value)

def commit_after(fn):
	def call(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		finally:
			if transaction.is_dirty():
				transaction.commit()
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call
	
class ChangesetMixin:
	def beginChanges(self):
		self._nosave = getattr(self, "_nosave", 0) + 1
		#print "nosave %d" % self._nosave
	def endChanges(self):
		self._nosave = getattr(self, "_nosave", 1) - 1
		#print "nosave %d" % self._nosave
		if self._nosave == 0:
			del self._nosave
			self.save()
	def save(self):
		if not hasattr(self, "_nosave"):
			#print "%s save" % self 
			models.Model.save(self)

def changeset(fn):
	def call(*args, **kwargs):
		args[0].beginChanges()
		try:
			return fn(*args, **kwargs)
		finally:
			args[0].endChanges()
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call
	
class ReloadMixin:
	def reload(self):
		obj = self.__class__.objects.get(pk=self.pk)
		self.__dict__ = obj.__dict__
		return self
						
nameValidator = validators.RegexValidator(regex="^[a-zA-Z0-9_-]{2,}$")
templateValidator = validators.RegexValidator(regex="^[a-zA-Z0-9_.]+-[a-zA-Z0-9_.]+$")
ifaceValidator = validators.RegexValidator(regex="^eth\d+$")