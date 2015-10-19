from __future__ import print_function
from mongoengine import *
from mongoengine.base.fields import BaseField
import bson, sys

# noinspection PyUnresolvedReferences

class _DummyDoesNotExist(Exception):
	pass
class _DummyMultipleObjectsReturned(Exception):
	pass
class _DummyQuerySetManager(QuerySetManager):
	def __init__(self):
		QuerySetManager.__init__(self)
	def get(self, *args, **kwargs):
		raise NotImplemented()

class ReferenceFieldId(object):
	def __init__(self, referenceField, asString=True):
		assert isinstance(referenceField, (ReferenceField, GenericReferenceField))
		self.field = referenceField
		self.asString = asString
	def __get__(self, instance, owner):
		# noinspection PyCallByClass
		data = BaseField.__get__(self.field, instance, owner)
		if isinstance(self.field, GenericReferenceField) and isinstance(data, dict) and '_ref' in data:
			data = data['_ref']
		if data is None: return None
		oid = data.id if isinstance(data, bson.DBRef) else data.pk
		return str(oid) if self.asString else oid

class ExtDocument(object):
	# Fix PyCharm inspection
	objects = _DummyQuerySetManager()
	DoesNotExist = _DummyDoesNotExist
	MultipleObjectsReturned = _DummyMultipleObjectsReturned
	id = 1
	save = None
	del objects, DoesNotExist, MultipleObjectsReturned, id, save

	@property
	def idStr(self):
		return str(self.id) if self.id else None

	def getFieldId(self, field, asString=False):
		# noinspection PyUnresolvedReferences
		dat = self._data.get(field)
		if isinstance(dat, dict) and '_ref' in dat:
			dat = dat['_ref']
		if dat is None:
			return None
		if isinstance(dat, bson.DBRef):
			# noinspection PyProtectedMember
			return str(dat._DBRef__id) if asString else dat._DBRef__id
		return str(dat.id) if asString else dat.id


class BaseDocument(ExtDocument, Document):
	meta = {'abstract': True}

	def __init__(self, *args , **kwargs):
		Document.__init__(self, *args, **kwargs)
		for key, value in kwargs.items():
			if key.startswith('_'):
				continue
			if key in self._fields:
				continue
			print("Warning: value set on untracked field: %s.%s = %r" % (self.__class__.__name__, key, value), file=sys.stderr)

	def __setattr__(self, key, value):
		if key.startswith('_') or key in ['id'] or hasattr(self, key) or (key.startswith('get_') and key.endswith('_display')):
			Document.__setattr__(self, key, value)
		else:
			print("Warning: value set on untracked field: %s.%s = %r" % (self.__class__.__name__, key, value), file=sys.stderr)


class DataEntry(BaseDocument):
	key = StringField(unique=True)
	value = DynamicField()
	meta = {
		'indexes': ['key'], 'collection': 'key_value_store'
	}

	def __str__(self):
		return "%s=%r" % (self.key, self.value)

class DataHub:
	def __getitem__(self, item):
		return DataEntry.objects.get(key=item).value
	def get(self, item, default=None):
		try:
			return self[item]
		except DataEntry.DoesNotExist:
			return default
	def set(self, key, value):
		try:
			entry = DataEntry.objects.get(key=key)
			entry.value = value
			entry.save()
		except DataEntry.DoesNotExist:
			DataEntry(key=key, value=value).save()
	def __setitem__(self, key, value):
		self.set(key, value)

data = DataHub()