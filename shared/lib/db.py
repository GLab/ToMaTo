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

from . import anyjson as json
from django.db import models, transaction
from django import db
from django.core import validators
from .. import config

"""
A :class:`TextField` that stores serialized data in the form of JSON.  You can
set th"is field to be any Python data structure that contains data that can be
serialized by the ``simplejson`` serializer, in addition to DateTime objects,
which can be serialized even though upon deserialization they will remain
strings.
"""

class JSONField(models.TextField):
	description = "Data that serializes and deserializes into and out of JSON."

	# Used so to_python() is called
	__metaclass__ = models.SubfieldBase

	def _dumps(self, data):
		return json.dumps(data)

	def _loads(self, str_):
		if config.MAINTENANCE:
			return str_
		return json.loads(str_)

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

def wrap_task(fn):
	def call(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		finally:
			if transaction.is_dirty():
				transaction.commit()
				db.connections.all()[0].close()
			db.close_old_connections()
	call.__module__ = fn.__module__
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call

def commit_after(fn):
	def call(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		finally:
			if transaction.is_dirty():
				transaction.commit()
	call.__module__ = fn.__module__
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