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

import time, crypt, string, random, sys, hashlib, random
from .generic import *
from .db import *
from .lib import logging, util, mail #@UnresolvedImport
from . import scheduler
from .lib.settings import settings, Config
from .lib.error import UserError, InternalError

from .lib.userflags import Flags


USER_ATTRS = ["realname", "email", "password"]

class Notification(EmbeddedDocument):
	id = StringField(required=True)
	timestamp = FloatField(required=True)
	title = StringField(required=True)
	message = StringField(required=True)
	read = BooleanField(default=False)
	ref_obj = ListField(StringField())
	sender = StringField()
	subject_group = StringField()

	def init(self, ref, sender, subject_group=None):
		self.ref_obj = ref if ref else []
		self.sender = sender.name if sender else None
		self.subject_group = subject_group

	def info(self):
		return {
			'id': self.id,
			'timestamp': self.timestamp,
			'title': self.title,
			'message': self.message,
			'read': self.read,
			'ref': self.ref_obj if self.ref_obj else None,
			'sender': self.sender,
			'subject_group': self.subject_group
		}

	def set_read(self, read):
		self.read = read

class User(Entity, BaseDocument):
	"""
	:type organization: organization.Organization
	:type quota: quota.Quota
	:type flags: list
	:type clientData: dict
	:type notifications: list of Notification
	"""
	from .organization import Organization
	from .quota import Quota

	name = StringField(required=True)
	organization = ReferenceField(Organization, required=True, reverse_delete_rule=DENY)
	password = StringField(required=True)
	lastLogin = FloatField(db_field='last_login', required=True)
	quota = EmbeddedDocumentField(Quota, required=True)
	realname = StringField()
	email = EmailField()
	flags = ListField(StringField())
	notifications = ListField(EmbeddedDocumentField(Notification))
	clientData = DictField(db_field='client_data')
	_origin = StringField(db_field="origin")
	_passwordTime = FloatField(db_field='password_time')
	meta = {
		'ordering': ['name'],
		'indexes': [
			'lastLogin', 'flags', 'organization', 'name'
		]
	}

	@classmethod
	def create(cls, name, organization, email, password=None, attrs=None):
		if not password:
			password = User.randomPassword()
		if not attrs:
			attrs = {}
		from .quota import Quota, Usage
		default_quota = settings.get_user_quota(Config.USER_QUOTA_DEFAULT)
		obj = cls(lastLogin=time.time(),
		          password=password,
							quota=Quota(
								used=Usage(cputime=0, memory=0, diskspace=0, traffic=0),
								monthly=Usage.from_settings(default_quota),
								continousFactor=default_quota["continous-factor"],
								usedTime=time.time()
								)
							)
		try:
			obj.modify(name=name, organization=organization, email=email, **attrs)
			obj.modify_password(password)
			obj.save()
		except:
			if obj.id:
				obj.remove()
			raise
		return obj

	def _remove(self):
		logging.logMessage("remove", category="user", name=self.name)
		if self.id:
			self.delete()

	def __str__(self):
		return self.name

	def __repr__(self):
		return "User(%s)" % self.name

	@classmethod
	def hashPassword(cls, password):
		saltchars = string.ascii_letters + string.digits + './'
		salt = "$1$"
		salt += ''.join([ random.choice(saltchars) for _ in range(8) ])
		return crypt.crypt(password, salt)

	@classmethod
	def randomPassword(cls):
		return ''.join(random.choice(2 * string.ascii_lowercase + string.ascii_uppercase + 2 * string.digits) for x in range(12))

	def checkPassword(self, password):
		return self.password == crypt.crypt(password, self.password)

	@classmethod
	def get(cls, name, **kwargs):
		"""
		:rtype : User
		"""
		try:
			return User.objects.get(name=name, **kwargs)
		except User.DoesNotExist:
			return None

	def modify_organization(self, val):
		from .organization import Organization
		orga = Organization.get(val)
		UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist", data={"name": val})
		self.organization = orga

	def modify_quota(self, val):
		self.quota.modify(val)

	def modify_password(self, password):
		self.password = User.hashPassword(password)
		self.save()

	def modify_flags(self, flags):
		UserError.check(isinstance(flags, dict), code=UserError.INVALID_DATA, message="flags must be a dictionary")
		for flag, is_set in flags.iteritems():
			if (not is_set) and (flag in self.flags):
				self.flags.remove(flag)
			if (is_set) and (flag not in self.flags):
				self.flags.append(flag)





	#clientData
	def setUnknownAttributes(self, attrs):
		for key, value in attrs.iteritems():
			InternalError.check(key.startswith("_"), code=InternalError.INVALID_PARAMETER, message="internally modifying invalid argument", data={key: value})
			self.clientData[key[1:]] = value

	def checkUnknownAttribute(self, key, value):
		if key.startswith("_"):
			return True
		return super(User, self).checkUnknownAttribute(key, value)

	def info(self):
		res = super(User, self).info()
		for key, value in self.clientData.iteritems():
			res["_"+key] = value
		return res





	def send_message(self, fromUser, subject, message, ref=None, subject_group=None):
		# add notification
		now = time.time()
		notf_id = hashlib.sha256(repr({
			'title': subject,
			'message': message,
			'ref': ref,
			'fromUser': fromUser.name if fromUser else None,
			'subject_group': subject_group,
			'timestamp': now
		})).hexdigest()
		notf = Notification(title=subject, message=message, timestamp=now, id=notf_id)
		notf.init(ref, fromUser, subject_group)
		self.notifications.append(notf)
		self.save()

		# send email
		if Flags.NoMails not in self.flags:
			mail.send(self.realname, self.email, subject, message, fromUser.realname if fromUser else None)


	def notification_list(self, include_read=False):
		return [n.info() for n in self.notifications if (include_read or not n.read)]

	def notification_get(self, notification_id):
		for n in self.notifications:
			if n.id == notification_id:
				return n
		UserError.check(False, code=UserError.ENTITY_DOES_NOT_EXIST, message="Notification with that id does not exist", data={"id": notification_id, "user": self.name})

	def notification_set_read(self, notification_id, read=True):
		notif = self.notification_get(notification_id)
		notif.read = read
		self.save()

	def clean_up_notifications(self):
		border_read = time.time() - 60*60*24*30  # fixme: should be configurable
		border_unread = time.time() - 60*60*24*180  # fixme: should be configurable
		for n in list(self.notifications):
			if n.timestamp < (border_read if n.read else border_unread):
				self.notifications.remove(n)
		self.save()

	ACTIONS = {
		Entity.REMOVE_ACTION: Action(fn=_remove),
	}
	ATTRIBUTES = {
		"id": Attribute(get=lambda self: self.name),
		"name": Attribute(field=name, schema=schema.Identifier(minLength=3)),
		"realname": Attribute(field=realname, schema=schema.String(minLength=3)),
		"email": Attribute(field=email, schema=schema.Email()),
		"flags": Attribute(field=flags, set=modify_flags),
		"organization": Attribute(get=lambda self: self.organization.name, set=modify_organization),
		"quota": Attribute(get=lambda self: self.quota.info(), set=modify_quota),
		"notification_count": Attribute(get=lambda self: len(filter(lambda n: not n.read, self.notifications))),
		"last_login": Attribute(get=lambda self: self.lastLogin),
		"password_hash": Attribute(field=password)
	}


def clean_up_user_notifications(username):
	user = User.get(username)
	if user is not None:
		user.clean_up_notifications()

def get_all_usersnames():
	return [u.name for u in User.objects.all()]

def init():
	scheduler.scheduleMaintenance(3600*24, get_all_usersnames, clean_up_user_notifications)
