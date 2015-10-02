from ..db import *
from .. import currentUser
from ..lib import logging
from ..lib.error import UserError
from ..generic import *

class Site(Entity, BaseDocument):
	name = StringField(unique=True, required=True)
	from .organization import Organization
	organization = ReferenceField(Organization, required=True, reverse_delete_rule=DENY)
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

	def checkPermissions(self, *args, **kwargs):
		user = currentUser()
		if user.hasFlag(Flags.GlobalHostManager):
			return True
		if user.hasFlag(Flags.OrgaHostManager) and user.organization == self.organization:
			return True
		return False

	def modify_geolocation(self, value):
		if isinstance(value, dict):
			value = (value.get('latitude'), value.get('longitude'))
		self.geolocation = value

	def modify_organization(self, value):
		orga = Organization.get(value)
		UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
			data={"name": value})
		self.organization = orga

	def _checkRemove(self):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		if self.id:
			UserError.check(not self.hosts.all(), code=UserError.NOT_EMPTY, message="Site still has hosts")

	def _remove(self):
		logging.logMessage("remove", category="site", name=self.name)
		self.delete()

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=_remove, check=_checkRemove)
	}
	ATTRIBUTES = {
		"name": Attribute(field=name, check=checkPermissions, schema=schema.Identifier()),
		"label": Attribute(field=label, check=checkPermissions, schema=schema.String()),
		"location": Attribute(field=location, check=checkPermissions, schema=schema.String()),
		"geolocation": Attribute(
			get=lambda obj: {'latitude': obj.geolocation[0], 'longitude': obj.geolocation[1]} if obj.geolocation else None,
			set=lambda obj, value: obj.modify_geolocation(value),
			check=checkPermissions
		),
		"organization": Attribute(
			get=lambda obj: obj.organization.name,
			set=lambda obj, value: obj.modify_organization(value),
			check=checkPermissions, schema=schema.Identifier()
		),
		"description": Attribute(field=description, check=checkPermissions, schema=schema.String())
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
		from .organization import Organization
		orga = Organization.get(organization)
		UserError.check('/' not in name, code=UserError.INVALID_VALUE, message="Site name may not include a '/'")
		UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
			data={"name": organization})
		user = currentUser()
		UserError.check(user.hasFlag(Flags.GlobalHostManager) or user.hasFlag(Flags.OrgaHostManager) and user.organization == orga,
			code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("create", category="site", name=name, label=label)
		site = Site(name=name, organization=orga, label=label)
		try:
			site.init(attrs)
			site.save()
		except:
			site.remove()
			raise
		return site

from .organization import Organization
from ..auth import Flags