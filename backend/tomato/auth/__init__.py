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

import time, crypt, string, random, sys
from ..db import *
from ..lib import logging, util, mail #@UnresolvedImport
from .. import config, currentUser, setCurrentUser, scheduler, accounting
from ..lib.error import UserError

class Flags:
	Debug = "debug"
	ErrorNotify = "error_notify"
	NoTopologyCreate = "no_topology_create"
	OverQuota = "over_quota"
	NewAccount = "new_account"
	RestrictedProfiles = "restricted_profiles"
	RestrictedTemplates ="restricted_templates"
	RestrictedNetworks ="restricted_networks"
	NoMails = "nomails"
	GlobalAdmin = "global_admin" #alle rechte für alle vergeben
	GlobalHostManager = "global_host_manager"
	GlobalToplOwner = "global_topl_owner"
	GlobalToplManager = "global_topl_manager"
	GlobalToplUser = "global_topl_user"	
	GlobalHostContact = "global_host_contact"
	GlobalAdminContact = "global_admin_contact"
	OrgaAdmin = "orga_admin" #nicht "global-" rechte vergeben für eigene user (auch nicht debug)
	OrgaHostManager = "orga_host_manager" # eigene orga, hosts und sites verwalten
	OrgaToplOwner = "orga_topl_owner"
	OrgaToplManager = "orga_topl_manager"
	OrgaToplUser = "orga_topl_user"	
	OrgaHostContact = "orga_host_contact"
	OrgaAdminContact = "orga_admin_contact"

flags = {
	Flags.Debug: "Debug: See everything",
	Flags.ErrorNotify: "ErrorNotify: receive emails for new kinds of errors",
	Flags.NoTopologyCreate: "NoTopologyCreate: Restriction on topology_create",
	Flags.OverQuota: "OverQuota: Restriction on actions start, prepare and upload_grant",
	Flags.NewAccount: "NewAccount: Account is new, just a tag",
	Flags.RestrictedProfiles: "RestrictedProfiles: Can use restricted profiles",
	Flags.RestrictedTemplates:"RestrictedTemplates: Can use restricted templates",
	Flags.RestrictedNetworks:"RestrictedNetworks: Can use restricted Networks",
	Flags.NoMails: "NoMails: Can not receive mails at all",
	Flags.GlobalAdmin: "GlobalAdmin: Modify all accounts",
	Flags.GlobalHostManager: "GlobalHostsManager: Can manage all hosts and sites",
	Flags.GlobalToplOwner: "GlobalToplOwner: Owner for every topology",
	Flags.GlobalToplManager: "GlobalToplManager: Manager for every topology",
	Flags.GlobalToplUser: "GlobalToplUser: User for every topology",
	Flags.GlobalHostContact: "GlobalHostContact: User receives mails about host problems",
	Flags.GlobalAdminContact: "GlobalAdminContact: User receives mails to administrators",
	Flags.OrgaAdmin: "OrgaAdmin: Modify all accounts of a specific organization",
	Flags.OrgaHostManager: "OrgaHostsManager: Can manage all hosts and sites of a specific organization",
	Flags.OrgaToplOwner: "OrgaToplOwner: Owner for every topology of a specific organization",
	Flags.OrgaToplManager: "OrgaToplManager: Manager for every topology of a specific organization",
	Flags.OrgaToplUser: "OrgaToplUser: User for every topology of a specific organization",
	Flags.OrgaHostContact: "OrgaHostContact: User receives mails about host problems of a specific organization",
	Flags.OrgaAdminContact: "OrgaAdminContact: User receives mails to a specific organization"
}

categories = [
			{'title': 'manager_user_global',
			 'onscreentitle': 'Global User Management',
			 'flags': [
						Flags.GlobalAdmin,
						Flags.GlobalToplOwner,
						Flags.GlobalToplManager,
						Flags.GlobalToplUser,
						Flags.GlobalAdminContact
						]},
			{'title': 'manager_user_orga',
			 'onscreentitle': 'Organization-Internal User Management',
			 'flags': [
						Flags.OrgaAdmin,
						Flags.OrgaToplOwner,
						Flags.OrgaToplManager,
						Flags.OrgaToplUser,
						Flags.OrgaAdminContact
						]},
			{'title': 'manager_host_global',
			 'onscreentitle': 'Global Host Management',
			 'flags': [
						Flags.GlobalHostManager,
						Flags.GlobalHostContact
						]},
			{'title': 'manager_host_orga',
			 'onscreentitle': 'Organization-Internal Host Management',
			 'flags': [
						Flags.OrgaHostManager,
						Flags.OrgaHostContact
						]},
			{'title': 'error_management',
			 'onscreentitle': 'Error Management',
			 'flags': [
						Flags.Debug,
						Flags.ErrorNotify
						]},
			{'title': 'user',
			 'onscreentitle': 'User Settings',
			 'flags': [
						Flags.NoTopologyCreate,
						Flags.OverQuota,
						Flags.RestrictedProfiles,
						Flags.RestrictedTemplates,
						Flags.RestrictedNetworks,
						Flags.NewAccount,
						Flags.NoMails
						]}
			]
		

orga_admin_changeable = [Flags.NoTopologyCreate, Flags.OverQuota, Flags.NewAccount, 
						Flags.RestrictedProfiles, Flags.RestrictedTemplates, Flags.RestrictedNetworks, Flags.NoMails, Flags.OrgaAdmin, Flags.OrgaHostManager,
						Flags.OrgaToplOwner, Flags.OrgaToplManager, Flags.OrgaToplUser, 
						Flags.OrgaHostContact, Flags.OrgaAdminContact]
global_pi_flags = [Flags.GlobalAdmin, Flags.GlobalToplOwner, Flags.GlobalAdminContact]
global_tech_flags = [Flags.GlobalHostManager, Flags.GlobalHostContact]
orga_pi_flags = [Flags.OrgaAdmin, Flags.OrgaToplOwner, Flags.OrgaAdminContact]
orga_tech_flags = [Flags.OrgaHostManager, Flags.OrgaHostContact]

USER_ATTRS = ["realname", "email", "password"]

class Notification(EmbeddedDocument):
	id = StringField(required=True, unique=True)
	timestamp = FloatField(required=True)
	title = StringField(required=True)
	message = StringField(required=True)
	read = BooleanField(default=False)
	ref_obj = ListField(StringField())
	sender = StringField()

	def init(self, ref, sender):
		self.ref_obj = ref if ref else []
		print self.ref_obj
		self.sender = sender.name if sender else None

	def info(self):
		return {
			'id': self.id,
			'timestamp': self.timestamp,
			'title': self.title,
			'message': self.message,
			'read': self.read,
			'ref': self.ref_obj if self.ref_obj else None,
			'sender': self.sender
		}

	def set_read(self, read):
		self.read = read

class User(BaseDocument):
	"""
	:type organization: host.Organization
	:type totalUsage: accounting.UsageStatistics
	:type quota: accounting.Quota
	:type flags: list
	:type clientData: dict
	:type notifications: list of Notification
	"""
	from ..host.organization import Organization
	from ..accounting import Quota, UsageStatistics
	name = StringField(required=True, unique_with='origin')
	origin = StringField(required=True)
	organization = ReferenceField(Organization, required=True, reverse_delete_rule=DENY)
	password = StringField(required=True)
	passwordTime = FloatField(db_field='password_time', required=True)
	lastLogin = FloatField(db_field='last_login', required=True)
	totalUsage = ReferenceField(UsageStatistics, db_field='total_usage', required=True, reverse_delete_rule=DENY)
	quota = EmbeddedDocumentField(Quota, required=True)
	realname = StringField()
	email = EmailField()
	flags = ListField(StringField())
	notifications = ListField(EmbeddedDocumentField(Notification))
	clientData = DictField(db_field='client_data')
	meta = {
		'ordering': ['name'],
		'indexes': [
			'lastLogin', 'passwordTime', 'flags', 'organization', ('name', 'origin')
		]
	}
	@property
	def topologies(self):
		from ..topology import Topology
		return Topology.objects(permissions__user=self)

	@classmethod	
	def create(cls, name, organization, password, flags, origin, **kwargs):
		from ..host.organization import Organization
		from ..accounting import Quota, UsageStatistics
		orga = Organization.get(organization)
		UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist", data={"name": organization})
		user = User(name=name, organization=orga, flags=flags, origin=origin)
		setCurrentUser(user)
		user.modify(kwargs, save=False)
		user.storePassword(password)
		user.lastLogin = time.time()
		user.quota = Quota()
		user.quota.init(**config.DEFAULT_QUOTA)
		stats = UsageStatistics()
		stats.init()
		user.totalUsage = stats
		user.save()
		return user

	def sendNotification(self, subject, message, ref=None, fromUser=None, send_email=True):
		self._addNotification(subject, message, ref, fromUser)
		if send_email:
			self._sendMail(subject, message, fromUser)

	def _addNotification(self, title, message, ref, fromUser):
		now = time.time()
		notf = Notification(title=title, message=message, timestamp=now, id=str(now))
		notf.init(ref, fromUser)
		self.notifications.append(notf)
		self.save()

	def _sendMail(self, subject, message, fromUser=None):
		if not self.email or self.hasFlag(Flags.NoMails):
			logging.logMessage("failed to send mail", category="user", subject=subject)
			return
		data = {"subject": subject, "message": message, "realname": self.realname or self.name}
		subject = config.EMAIL_SUBJECT_TEMPLATE % data
		message = config.EMAIL_MESSAGE_TEMPLATE % data
		from_ = None
		if fromUser:
			from_ = "%s <%s>" % (fromUser.realname or fromUser.name, fromUser.email)
		mail.send("%s <%s>" % (self.realname or self.name, self.email), subject, message, from_=from_)

	def _get_notification(self, notification_id):
		for n in self.notifications:
			if n.id == notification_id:
				return n

	def set_notification_read(self, notification_id, read):
		notf = self._get_notification(notification_id)
		UserError.check(notf, code=UserError.INVALID_VALUE, message="Notification does not exist", todump=False, data={'notification_id': notification_id})
		notf.set_read(read)
		self.save()

	def clean_up_notifications(self):
		"""
		This removes old notifications.
		read notifications older than 30 days
		unread notifications older than 180 days
		:return:
		"""
		border_read = time.time() - 60*60*24*30
		border_unread = time.time() - 60*60*24*180
		for n in list(self.notifications):
			if n.timestamp < (border_read if n.read else border_unread):
				self.notifications.remove(n)
		self.save()

	def checkPassword(self, password):
		return self.password == crypt.crypt(password, self.password)

	def storePassword(self, password):
		saltchars = string.ascii_letters + string.digits + './'
		salt = "$1$"
		salt += ''.join([ random.choice(saltchars) for _ in range(8) ])
		self.password = crypt.crypt(password, salt)
		self.passwordTime = time.time()

	def forgetPassword(self):
		self.password = None
		self.passwordTime = None
		self.save()		
		
	def updateFrom(self, other):
		if not self.email and other.email:
			self.email = other.email
		if not self.realname and other.realname:
			self.realname = other.realname
		self.save()
	
	def loggedIn(self):
		logging.logMessage("successful login", category="auth", user=self.name, origin=self.origin)
		self.lastLogin = time.time()
		self.save()
	
	def hasFlag(self, flag):
		return flag in self.flags
	
	def addFlag(self, flag):
		if self.hasFlag(flag):
			return		
		logging.logMessage("add_flag", category="user", name=self.name, origin=self.origin, flag=flag)	
		self.flags.append(flag)
		self.save()
		
	def removeFlag(self, flag):
		if not self.hasFlag(flag):
			return
		logging.logMessage("remove_flag", category="user", name=self.name, origin=self.origin, flag=flag)	
		self.flags.remove(flag)
		self.save()

	def modify_password(self, password):
		for prov in providers:
			if not prov.getName() == self.origin:
				continue
			UserError.check(prov.canChangePassword(), code=UserError.INVALID_CONFIGURATION, message="Provider can not change password")
			prov.changePassword(self.name, password)
			self.storePassword(password)

	def modify_organization(self, value):
		from ..host.organization import Organization
		orga = Organization.get(value)
		UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist", data={"name": value})
		self.organization=orga
		
	def modify_quota(self, value):
		self.quota.modify(value)

	def isAdminOf(self, user):
		if self.hasFlag(Flags.GlobalAdmin):
			return True
		return self.hasFlag(Flags.OrgaAdmin) and self.organization == user.organization and not user.hasFlag(Flags.GlobalAdmin)

	def can_modify(self, attr, value):
		if attr.startswith("_"):
			return True
		if attr in USER_ATTRS:
			return True
		user = currentUser()
		if user.hasFlag(Flags.GlobalAdmin):
			if user == self and attr == "flags" and not Flags.GlobalAdmin in value:
				# Admins must not delete their own admin flag
				return False
			return True
		if user.isAdminOf(self):
			if attr in ["name"]:
				return True
			if attr == "flags":
				changedFlags = (set(value) - set(self.flags)) | (set(self.flags) - set(value)) 
				for flag in changedFlags:
					if not flag in orga_admin_changeable:
						return False
				return True
		return False

	def modify(self, attrs, save=True):
		logging.logMessage("modify", category="user", name=self.name, origin=self.origin, attrs=attrs)
		for key, value in attrs.items():
			UserError.check(self.can_modify(key, value), code=UserError.DENIED,
				message="No permission to change attribute", data={"attribute": key})
			if key.startswith("_"):
				self.clientData[key[1:]] = value
				continue
			if hasattr(self, "modify_%s" % key):
				getattr(self, "modify_%s" % key)(value)
			else:
				setattr(self, key, value)
		if save:
			self.save()

	def list_notifications(self, include_read=False):
		return [n.info() for n in self.notifications if (include_read or not n.read)]

	def get_notification(self, notification_id):
		return self._get_notification(notification_id).info()
	
	def info(self, includeInfos):
		info = {
			"name": self.name,
			"origin": self.origin,
			"organization": self.organization.name,
			"id": "%s@%s" % (self.name, self.origin),
			"realname": self.realname,
			"email": self.email,
			"flags": list(self.flags),
			"notification_count": len(filter(lambda n: not n.read, self.notifications))
		}
		info.update({"_"+k: v for k, v in self.clientData.items()})
		if not includeInfos:
			del info["email"]
			del info["flags"]
			del info["notification_count"]
		else:
			info["quota"] = self.quota.info()
		return info
		
	def updateUsage(self):
		#FIXME: do something useful with topologies with multiple owners
		self.totalUsage.updateFrom([top.totalUsage for top in self.topologies.filter(permissions__role="owner")])
		
	def updateQuota(self):
		self.quota.updateUsage(self.totalUsage)
		self.save()
		
	def enforceQuota(self):
		if not self.hasFlag(Flags.NewAccount):
			if self.quota.getFactor() >= 1.0:
				self.addFlag(Flags.OverQuota)
			else:
				self.removeFlag(Flags.OverQuota)
		#FIXME: send warning emails, etc
		
	def __str__(self):
		return self.__unicode__()

	def __unicode__(self):
		return "%s@%s" % ( self.name, self.origin )


class Provider:
	def __init__(self, name, options):
		self.name = name
		self.options = options
		self.parseOptions(**options)
	def parseOptions(self, **kwargs):
		pass
	def canRegister(self):
		return False
	def register(self, username, password, organization, attrs):
		raise Exception("not supported")
	def canChangePassword(self):
		return False
	def changePassword(self, username, password):
		raise Exception("not supported")
	def getName(self):
		return self.name
	def getAccountTimeout(self):
		return self.options.get("account_timeout", 0)
	def getPasswordTimeout(self):
		return self.options.get("password_timeout", 0)
	def getUsers(self, **kwargs):
		return User.objects.filter(origin=self.name, **kwargs)
	def cleanup(self):
		if self.getPasswordTimeout():
			for user in self.getUsers(passwordTime__lte = time.time() - self.getPasswordTimeout()):
				logging.logMessage("password cache timeout", category="auth", user=user.name)
				user.forgetPassword()
		if self.getAccountTimeout():
			for user in self.getUsers(lastLogin__lte = time.time() - self.getAccountTimeout()):
				logging.logMessage("account timeout", category="auth", user=user.name)
				user.remove()


def getUser(name):
	origin = None
	if "@" in name:
		name, origin = name.split("@", 1)
	try:
		if not origin is None:
			return User.objects.get(name=name, origin=origin)
		else:
			return User.objects.get(name=name)
	except User.DoesNotExist:
		return None
	except User.MultipleObjectsReturned:
		raise UserError(code=UserError.AMBIGUOUS, message="Multiple users with that name exist, specify origin")

def getFilteredUsers(filterfn, organization = None):
	return filter(filterfn, getAllUsers(organization))

def getFlaggedUsers(flag):
	return getFilteredUsers(lambda user: user.hasFlag(flag))

def notifyFilteredUsers(filterfn, subject, message, organization = None, ref=None):
	for user in getFilteredUsers(filterfn, organization):
		user.sendNotification(subject, message, ref=ref)

def notifyFlaggedUsers(flag, subject, message, organization=None, ref=None):
	notifyFilteredUsers(lambda user: user.hasFlag(flag), subject, message, organization, ref)
	
def notifyAdmins(subject, text, global_contact = True, issue="admin"):
	user = currentUser()
	flag = None
	
	if global_contact:
		if issue=="admin":
			flag = Flags.GlobalAdminContact
		if issue=="host":
			flag = Flags.GlobalHostContact
	else:
		if issue=="admin":
			flag = Flags.OrgaAdminContact
		if issue=="host":
			flag = Flags.OrgaHostContact
	UserError.check(flag, code=UserError.INVALID_VALUE, message="Issue does not exist", data={"issue": issue})
	
	notifyFlaggedUsers(flag, "Message from %s: %s" % (user.name, subject), "The user %s <%s> has sent a message to all administrators.\n\nSubject:%s\n%s" % (user.name, user.email, subject, text), organization=user.organization, ref=None)
	
def sendMessage(user, subject, text):
	from_ = currentUser()
	to = getUser(user)
	UserError.check(to, code=UserError.ENTITY_DOES_NOT_EXIST, message="User not found")
	to.sendNotification(title="Message from %s: %s" % (from_.name, subject), message="The user %s has sent a message to you.\n\nSubject:%s\n%s" % (from_.name, subject, text), fromUser=from_)

def getAllUsers(organization = None):
	if organization is None:
		return User.objects.all()
	else:
		return User.objects.filter(organization=organization)

@util.wrap_task
def cleanup():
	for provider in providers:
		provider.cleanup()
	
def provider_login(username, password):
	for prov in providers:
		user = prov.login(username, password)
		if user:
			return user
	logging.logMessage("failed login", category="auth", user=username)
	return None

def login(username, password):
	for user in User.objects.filter(name = username):
		if user.password and user.checkPassword(password):
			user.loggedIn()
			return user
	user = provider_login(username, password)
	if not user:
		return None
	try:
		stored = User.objects.get(name=user.name, origin=user.origin)
		stored.updateFrom(user)
	except User.DoesNotExist:
		user.save()
		stored = user
	stored.storePassword(password)
	stored.loggedIn()
	return stored

def remove(user):
	user.delete()
	user.totalUsage.remove()

def register(username, password, organization, attrs=None, provider=""):
	if not attrs: attrs = {}
	for prov in providers:
		if not prov.getName() == provider:
			continue
		UserError.check(prov.canRegister(), code=UserError.INVALID_CONFIGURATION, message="Provider can not register users")
		user = prov.register(username, password, organization, attrs)
		setCurrentUser(user)
		return user
	raise UserError(code=UserError.INVALID_VALUE, message="No such provider", data={"provider": provider})

providers = []

scheduler.scheduleRepeated(300, cleanup) #every 5 minutes @UndefinedVariable


def _may_broadcast(account):
	if Flags.GlobalAdmin in account.flags:
		return True
	if Flags.OrgaAdmin in account.flags:
		return True
	if Flags.GlobalHostManager in account.flags:
		return True
	if Flags.OrgaHostManager in account.flags:
		return True
	return False


def send_announcement(sender, title, message, ref=None, show_sender=True):
	UserError.check(_may_broadcast(sender), code=UserError.DENIED, message="Not enough permissions to send announcements")
	if (Flags.GlobalAdmin in sender.flags) or (Flags.GlobalHostManager in sender.flags):
		receivers = getAllUsers()
	elif (Flags.OrgaAdmin in sender.flags) or (Flags.OrgaHostManager in sender.flags):
		receivers = getAllUsers(organization=sender.organization)
	else:
		receivers = []

	for acc in receivers:
		acc.sendNotification(title, message, ref, sender if show_sender else None, send_email=False)





def clean_up_all_notifications():
	for acc in User.objects.all():
		acc.clean_up_notifications()

def init():
	print >>sys.stderr, "Loading auth modules..."
	for conf in config.AUTH:
		provider = None #make eclipse shut up
		exec("import %s_provider as provider" % conf["provider"]) #pylint: disable-msg=W0122
		prov = provider.init(name=conf["name"], options=conf["options"])
		providers.append(prov)
		print >>sys.stderr, " - %s (%s)" % (conf["name"], conf["provider"])
	if not providers:
		print >>sys.stderr, "Warning: No authentication modules configured."
	scheduler.scheduleRepeated(60*60*24, clean_up_all_notifications, immediate=True)
