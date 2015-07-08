from ..db import *
from .. import currentUser
from ..accounting import UsageStatistics
from ..lib import logging
from ..lib.error import UserError

class Organization(BaseDocument):
	name = StringField(unique=True, required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True, reverse_delete_rule=DENY)
	label = StringField(required=True)
	homepageUrl = URLField(db_field='homepage_url')
	imageUrl = URLField(db_field='image_url')
	description = StringField()
	meta = {
		'ordering': ['name'],
		'indexes': [
			'name'
		]
	}
	@property
	def sites(self):
		from .site import Site
		return Site.objects(organization=self)
	@property
	def users(self):
		from ..auth import User
		return User.objects(organization=self)

	def init(self, attrs):
		self.totalUsage = UsageStatistics().save()
		self.modify(attrs)

	def checkPermissions(self):
		user = currentUser()
		if user.hasFlag(Flags.GlobalAdmin):
			return True
		if user.hasFlag(Flags.OrgaAdmin) and user.organization == self:
			return True
		return False

	def modify(self, attrs):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("modify", category="organization", name=self.name, attrs=attrs)
		for key, value in attrs.iteritems():
			if key == "label":
				self.label = value
			elif key == "homepage_url":
				self.homepageUrl = value
			elif key == "image_url":
				self.imageUrl = value
			elif key == "description":
				self.description = value
			else:
				raise UserError(code=UserError.UNSUPPORTED_ATTRIBUTE, message="Unknown organization attribute",
					data={"attribute": key})
		self.save()

	def remove(self):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		UserError.check(not self.sites, code=UserError.NOT_EMPTY, message="Organization still has sites")
		UserError.check(not self.users, code=UserError.NOT_EMPTY, message="Organization still has users")
		logging.logMessage("remove", category="organization", name=self.name)
		self.totalUsage.remove()
		self.delete()

	def updateUsage(self):
		self.totalUsage.updateFrom([user.totalUsage for user in self.users])

	def info(self):
		return {
			"name": self.name,
			"label": self.label,
			"homepage_url": self.homepageUrl,
			"image_url": self.imageUrl,
			"description": self.description
		}

	def __str__(self):
		return self.name

	def __repr__(self):
		return "Organization(%s)" % self.name

	@classmethod
	def get(cls, name, **kwargs):
		try:
			return Organization.objects.get(name=name, **kwargs)
		except Organization.DoesNotExist:
			return None

	@classmethod
	def create(cls, name, label=""):
		UserError.check(currentUser().hasFlag(Flags.GlobalAdmin), code=UserError.DENIED, message="Not enough permissions")
		logging.logMessage("create", category="site", name=name, label=label)
		organization = Organization(name=name, label=label)
		organization.save()
		return organization

from ..auth import Flags