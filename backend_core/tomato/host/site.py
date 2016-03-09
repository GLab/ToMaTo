from ..db import *
from ..lib import logging
from ..lib.error import UserError
from ..generic import *
from ..authorization.remote_info import get_organization_info

class Site(Entity, BaseDocument):
	name = StringField(unique=True, required=True)
	organization = StringField(required=True)
	label = StringField(required=True)
	location = StringField()
	geolocation = GeoPointField()
	description = StringField()
	meta = {
		'ordering': ['organization', 'name'],
		'indexes': [
			'organization', 'name'
		]
	}

	@property
	def hosts(self):
		from . import Host
		return Host.objects(site=self)

	def init(self, attrs):
		self.modify(attrs)

	def modify_geolocation(self, value):
		if isinstance(value, dict):
			value = (value.get('latitude'), value.get('longitude'))
		self.geolocation = value

	def modify_organization(self, value):
		UserError.check(get_organization_info(value).exists(), code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
			data={"name": value})
		self.organization = value

	def _checkRemove(self):
		if self.id:
			UserError.check(not self.hosts.all(), code=UserError.NOT_EMPTY, message="Site still has hosts")

	def _remove(self):
		logging.logMessage("remove", category="site", name=self.name)
		if self.id:
			self.delete()

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=_remove, check=_checkRemove)
	}
	ATTRIBUTES = {
		"name": Attribute(field=name, schema=schema.Identifier()),
		"label": Attribute(field=label, schema=schema.String()),
		"location": Attribute(field=location, schema=schema.String()),
		"geolocation": Attribute(
			get=lambda obj: {'latitude': obj.geolocation[0], 'longitude': obj.geolocation[1]} if obj.geolocation else None,
			set=lambda obj, value: obj.modify_geolocation(value)
		),
		"organization": Attribute(
			get=lambda obj: obj.organization.name,
			set=lambda obj, value: obj.modify_organization(value),
			schema=schema.Identifier()
		),
		"description": Attribute(field=description, schema=schema.String())
	}

	def __str__(self):
		return self.name

	def __repr__(self):
		return "Site(%s)" % self.name

	@classmethod
	def get(cls, name, **kwargs):
		try:
			return cls.objects.get(name=name, **kwargs)
		except Site.DoesNotExist:
			return None

	@classmethod
	def create(cls, name, organization, label="", attrs=None):
		if not attrs:
			attrs = {}
		UserError.check('/' not in name, code=UserError.INVALID_VALUE, message="Site name may not include a '/'")
		UserError.check(get_organization_info(organization).exists(), code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
			data={"name": organization})
		logging.logMessage("create", category="site", name=name, label=label)
		site = Site(name=name, organization=organization, label=label)
		try:
			attrs_ = attrs.copy()
			attrs_['name'] = name
			attrs_['label'] = label
			site.init(attrs_)
			site.save()
		except:
			site.remove()
			raise
		return site
