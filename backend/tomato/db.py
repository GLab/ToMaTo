from __future__ import print_function
from mongoengine import *
import bson

# noinspection PyUnresolvedReferences

class _DummyDoesNotExist(Exception):
	pass
class _DummyMultipleObjectsReturned(Exception):
	pass
class _DummyQuerySetManager(QuerySetManager):
	def __init__(self, Type=None):
		QuerySetManager.__init__(self)
		self.Type = Type
	def get(self, *args, **kwargs):
		return self.Type()

class ExtDocument(object):
	# Fix PyCharm inspection
	objects = _DummyQuerySetManager()
	DoesNotExist = _DummyDoesNotExist
	MultipleObjectsReturned = _DummyMultipleObjectsReturned
	id = 1
	save = None
	del objects, DoesNotExist, MultipleObjectsReturned, id, save

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

	def __setattr__(self, key, value):
		if key.startswith('_') or key in ['id'] or hasattr(self, key) or (key.startswith('get_') and key.endswith('_display')):
			Document.__setattr__(self, key, value)
		else:
			print("Warning: value set on untracked field: %s.%s = %r" % (self.__class__.__name__, key, value))

class DataEntry(BaseDocument):
	key = StringField(unique=True)
	value = DynamicField()
	meta = {
		'indexes': ['key'], 'collection': 'key_value_store'
	}

class DataHub:
	def __getattr__(self, item):
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
	def __setattr__(self, key, value):
		self.set(key, value)

data = DataHub()