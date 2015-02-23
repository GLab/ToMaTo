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
			if key == "description":
				self.label = value
			elif key == "location":
				self.location = value
			elif key == "geolocation":
				self.geolocation = value
			elif key == "description_text":
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
			"description": self.label,
			"location": self.location,
			"geolocation": self.geolocation,
			"organization": self.organization.name,
			"description_text": self.description
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
	def create(cls, name, organization, description=""):
		from .organization import Organization
		orga = Organization.get(organization)
		UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="No organization with that name",
			data={"name": organization})
		user = currentUser()
		UserError.check(user.hasFlag(Flags.GlobalHostManager) or user.hasFlag(Flags.OrgaHostManager) and user.organization == orga,
			code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("create", category="site", name=name, description=description)
		site = Site(name=name, organization=orga)
		site.save()
		site.init({"description": description})
		return site

from .organization import Organization
from ..auth import Flags