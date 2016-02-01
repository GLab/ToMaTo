from ..db import *
from .. import currentUser
from ..accounting import UsageStatistics
from ..lib import logging
from ..lib.error import UserError
from ..generic import *

class Organization(Entity, BaseDocument):
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

	def checkPermissions(self, *args, **kwargs):
		user = currentUser()
		if user.hasFlag(Flags.GlobalAdmin):
			return True
		if user.hasFlag(Flags.OrgaAdmin) and user.organization == self:
			return True
		return False

	def _checkRemove(self):
		UserError.check(self.checkPermissions(), code=UserError.DENIED, message="Not enough permissions")
		if self.id:
			UserError.check(not self.sites, code=UserError.NOT_EMPTY, message="Organization still has sites")
			UserError.check(not self.users, code=UserError.NOT_EMPTY, message="Organization still has users")

	def _remove(self):
		logging.logMessage("remove", category="organization", name=self.name)
		if self.id:
			self.delete()
		self.totalUsage.remove()

	def __str__(self):
		return self.name

	def __repr__(self):
		return "Organization(%s)" % self.name

	@classmethod
	def get(cls, name, **kwargs):
		"""
		:rtype : Organization
		"""
		try:
			return Organization.objects.get(name=name, **kwargs)
		except Organization.DoesNotExist:
			return None

	@classmethod
	def create(cls, name, label="", attrs=None):
		if not attrs:
			attrs = {}
		UserError.check(currentUser().hasFlag(Flags.GlobalAdmin), code=UserError.DENIED, message="Not enough permissions")
		UserError.check('/' not in name, code=UserError.INVALID_VALUE, message="Organization name may not include a '/'")
		logging.logMessage("create", category="site", name=name, label=label)
		organization = Organization(name=name, label=label)
		try:
			attrs_ = attrs.copy()
			attrs_['name'] = name
			attrs_['label'] = label
			organization.init(attrs_)
			organization.save()
		except:
			organization.remove()
			raise
		return organization

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=_remove, check=_checkRemove)
	}
	ATTRIBUTES = {
		"name": Attribute(field=name, check=checkPermissions, schema=schema.Identifier()),
		"label": Attribute(field=label, check=checkPermissions, schema=schema.String()),
		"homepage_url": Attribute(field=homepageUrl, check=checkPermissions, schema=schema.URL(null=True)),
		"image_url": Attribute(field=imageUrl, check=checkPermissions, schema=schema.URL(null=True)),
		"description": Attribute(field=description, check=checkPermissions, schema=schema.String())
	}


from ..auth import Flags