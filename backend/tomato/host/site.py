from ..db import *
from .. import currentUser
from ..lib import logging
from ..lib.error import UserError

class Site(BaseDocument):
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

	def checkPermissions(self):
		user = currentUser()
		if user.hasFlag(Flags.GlobalHostManager):
			return True
		if user.hasFlag(Flags.OrgaHostManager) and user.organization == self.organization:
			return True
		return False

	def modify(self, attrs):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("modify", category="site", name=self.name, attrs=attrs)
		for key, value in attrs.iteritems():
			if key == "label":
				self.label = value
			elif key == "location":
				self.location = value
			elif key == "geolocation":
				if isinstance(value, dict):
					value = (value.get('latitude'), value.get('longitude'))
				self.geolocation = value
			elif key == "description":
				self.description = value
			elif key == "organization":
				orga = Organization.get(value)
				UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
					data={"name": value})
				self.organization = orga
			else:
				raise UserError(code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unknown site attribute",
					data={"attribute": key})
		self.save()

	def remove(self):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		UserError.check(not self.hosts.all(), code=UserError.NOT_EMPTY, message="Site still has hosts")
		logging.logMessage("remove", category="site", name=self.name)
		self.delete()

	def info(self):
		return {
			"name": self.name,
			"label": self.label,
			"location": self.location,
			"geolocation": {'latitude': self.geolocation[0], 'longitude': self.geolocation[1]} if self.geolocation else None,
			"organization": self.organization.name,
			"description": self.description
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
	def create(cls, name, organization, label="", attrs={}):
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
		site.save()
		try:
			site.modify(attrs)
		except:
			site.remove()
			raise
		return site

from .organization import Organization
from ..auth import Flags