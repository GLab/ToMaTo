from .db import *
from .lib import logging
from .lib.error import UserError
from .generic import *
from .lib.service import get_backend_core_proxy

class Organization(Entity, BaseDocument):
	name = StringField(unique=True, required=True)
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
	def users(self):
		from .user import User
		return User.objects(organization=self)

	def _checkRemove(self):
		if self.id:
			UserError.check(not self.users, code=UserError.NOT_EMPTY, message="Organization still has users")
			UserError.check(not get_backend_core_proxy().site_list(organization=self.name),
			                code = UserError.NOT_EMPTY, message="Organization still has sites")

	def _remove(self):
		logging.logMessage("remove", category="organization", name=self.name)
		if self.id:
			self.delete()

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

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=_remove, check=_checkRemove)
	}
	ATTRIBUTES = {
		"name": Attribute(field=name, schema=schema.Identifier(minLength=3)),
		"label": Attribute(field=label, schema=schema.String(minLength=3)),
		"homepage_url": Attribute(field=homepageUrl, schema=schema.URL(null=True)),
		"image_url": Attribute(field=imageUrl, schema=schema.URL(null=True)),
		"description": Attribute(field=description, schema=schema.String(null=True))
	}