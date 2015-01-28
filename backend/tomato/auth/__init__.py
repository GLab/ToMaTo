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
from django.db import models
from ..lib import attributes, db, logging, util, mail #@UnresolvedImport
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

class User(attributes.Mixin, models.Model):
	from ..host import Organization
	name = models.CharField(max_length=255)
	origin = models.CharField(max_length=50)
	organization = models.ForeignKey(Organization, related_name="users")
	attrs = db.JSONField()
	password = models.CharField(max_length=250, null=True)
	password_time = models.FloatField(null=True)
	last_login = models.FloatField(default=time.time())
	totalUsage = models.OneToOneField(accounting.UsageStatistics, related_name='+', on_delete=models.PROTECT)
	quota = models.OneToOneField(accounting.Quota, related_name='+', on_delete=models.PROTECT)
	
	realname = attributes.attribute("realname", unicode)
	email = attributes.attribute("email", unicode)
	flags = attributes.attribute("flags", list, [])

	class Meta:
		db_table = "tomato_user"
		app_label = 'tomato'
		unique_together = (("name", "origin"),)
		ordering=["name", "origin"]

	@classmethod	
	def create(cls, name, organization, **kwargs):
		from ..host import getOrganization
		orga = getOrganization(organization)
		UserError.check(orga, code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist", data={"name": organization})
		user = User(name=name,organization=orga)
		user.attrs = kwargs
		user.last_login = time.time()
		return user

	def save(self, *args, **kwargs):
		if not hasattr(self, "totalUsage"):
			self.totalUsage = accounting.UsageStatistics.objects.create()
		if not hasattr(self, "quota"):
			quota = accounting.Quota()
			quota.init(config.DEFAULT_QUOTA["cputime"], config.DEFAULT_QUOTA["memory"], config.DEFAULT_QUOTA["diskspace"], config.DEFAULT_QUOTA["traffic"], config.DEFAULT_QUOTA["continous_factor"])
			self.quota = quota
		models.Model.save(self, *args, **kwargs)

	def _saveAttributes(self):
		pass #disable automatic attribute saving
	
	def checkPassword(self, password):
		return self.password == crypt.crypt(password, self.password)

	def storePassword(self, password):
		saltchars = string.ascii_letters + string.digits + './'
		salt = "$1$"
		salt += ''.join([ random.choice(saltchars) for _ in range(8) ])
		self.password = crypt.crypt(password, salt)
		self.password_time = time.time()
		self.save()
	
	def forgetPassword(self):
		self.password = None
		self.password_time = None
		self.save()		
		
	def updateFrom(self, other):
		if not self.email and other.email:
			self.email = other.email
		if not self.realname and other.realname:
			self.realname = other.realname
		self.save()
	
	def loggedIn(self):
		logging.logMessage("successful login", category="auth", user=self.name, origin=self.origin)
		self.last_login = time.time()
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
		from ..host import getOrganization
		orga = getOrganization(value)
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

	def modify(self, attrs):
		logging.logMessage("modify", category="user", name=self.name, origin=self.origin, attrs=attrs)
		for key, value in attrs.iteritems():
			UserError.check(self.can_modify(key, value), code=UserError.DENIED,
				message="No permission to change attribute", data={"attribute": key})
			if key.startswith("_"):
				self.attrs[key] = value
				continue
			if hasattr(self, "modify_%s" % key):
				getattr(self, "modify_%s" % key)(value)
			else:
				self.attrs[key] = value
		self.save()
	
	def info(self, includeInfos):
		info = {
			"name": self.name,
			"origin": self.origin,
			"organization": self.organization.name,
			"id": "%s@%s" % (self.name, self.origin) 
		}
		info.update(self.attrs)
		if not includeInfos:
			info["email"] = None
			info["flags"] = None
		else:
			info["quota"] = self.quota.info()
		return info
		
	def sendMail(self, subject, message, fromUser=None):
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
		
	def updateUsage(self):
		from .. import topology
		#FIXME: do something useful with topologies with multiple owners
		self.totalUsage.updateFrom([top.totalUsage for top in topology.getAll(permissions__entries__user=self, permissions__entries__role="owner")])
		
	def updateQuota(self):
		self.quota.update(self.totalUsage)
		
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
			for user in self.getUsers(password_time__lte = time.time() - self.getPasswordTimeout()):
				logging.logMessage("password cache timeout", category="auth", user=user.name)
				user.forgetPassword()
		if self.getAccountTimeout():
			for user in self.getUsers(last_login__lte = time.time() - self.getAccountTimeout()):
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

def mailFilteredUsers(filterfn, subject, message, organization = None):
	for user in getFilteredUsers(filterfn, organization):
		user.sendMail(subject, message)

def mailFlaggedUsers(flag, subject, message, organization=None):
	mailFilteredUsers(lambda user: user.hasFlag(flag), subject, message, organization)
	
def mailAdmins(subject, text, global_contact = True, issue="admin"):
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
	
	mailFlaggedUsers(flag, "Message from %s: %s" % (user.name, subject), "The user %s <%s> has sent a message to all administrators.\n\nSubject:%s\n%s" % (user.name, user.email, subject, text), organization=user.organization)
	
def mailUser(user, subject, text):
	from_ = currentUser()
	to = getUser(user)
	UserError.check(to, code=UserError.ENTITY_DOES_NOT_EXIST, message="User not found")
	to.sendMail("Message from %s: %s" % (from_.name, subject), "The user %s has sent a message to you.\n\nSubject:%s\n%s" % (from_.name, subject, text))

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
	usage = user.totalUsage
	quota = user.quota
	user.delete()
	usage.remove()
	quota.remove()

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
