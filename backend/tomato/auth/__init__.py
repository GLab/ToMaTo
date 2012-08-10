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

from tomato import config, fault
from tomato.lib import util
import time, atexit, datetime, crypt, string, random, sys, threading

from django.db import models

class User(models.Model):
	name = models.CharField(max_length=250)
	origin = models.CharField(max_length=250, null=True)
	is_user = models.BooleanField(default=True)
	is_admin = models.BooleanField(default=False)
	password = models.CharField(max_length=250, null=True)
	password_time = models.DateTimeField(null=True)
	email = models.EmailField(null=True)
	
	class Meta:
		db_table = "tomato_user"
		app_label = 'tomato'
		unique_together = (("name", "origin"),)
		ordering=["name", "origin"]

	def checkPassword(self, password):
		return self.password == crypt.crypt(password, self.password)

	def storePassword(self, password):
		saltchars = string.ascii_letters + string.digits + './'
		salt = "$1$"
		salt += ''.join([ random.choice(saltchars) for x in range(8) ])
		self.password = crypt.crypt(password, salt)
		self.password_time = datetime.datetime.now()
		self.save()

	def toDict(self):
		return {"name": self.name, "origin": self.origin, "is_user": self.is_user, "is_admin": self.is_admin}

	def sendMessage(self, subject, body):
		subject = config.MAIL["SUBJECT_PREFIX"] + subject + config.MAIL["SUBJECT_SUFFIX"]
		body = (config.MAIL["BODY_PREFIX"] % self.name) + body + config.MAIL["BODY_SUFFIX"]
		if self.email:
			util.sendMail(self.email, subject, body)
			print "Mail to %s: %s" % (self.email, subject)
		else:
			print "Cannot send message to %s, no email known" % str(self)

	def __str__(self):
		return self.__unicode__()

	def __unicode__(self):
		return "%s@%s" % ( self.name, self.origin ) if self.origin else self.name
		
timeout = datetime.timedelta(hours=config.LOGIN_TIMEOUT)

def getUser(name):
	origin = None
	if "@" in name:
		name, origin = name.split("@")
	try:
		if origin:
			return User.objects.get(name=name, origin=origin)
		else:
			return User.objects.get(name=name)
	except User.DoesNotExist:
		return None

def cleanup():
	#FIXME: delete users that have timed out and are unreferenced
	for user in User.objects.filter(password_time__lte = datetime.datetime.now() - timeout):
		user.password = None
		user.password_time = None
		user.save()
	
def provider_login(username, password):
	for prov in providers:
		user = prov.login(username, password)
		if user:
			user.origin = prov.name
			print "Successfull login: %s" % user.toDict()
			return user
	print "Failed login: %s" % username
	return None

def login(username, password):
	global _currentUser
	for user in User.objects.filter(name = username):
		if user.password and user.checkPassword(password):
			_currentUser.user = user
			return user
	user = provider_login(username, password)
	if not user:
		_currentUser.user = None
		return None
	try:
		stored = User.objects.get(models.Q(name=user.name) & (models.Q(origin=user.origin) | models.Q(origin=None)))
		stored.origin = user.origin
		stored.is_user = user.is_user
		stored.is_admin = user.is_admin
		if user.email:
			stored.email = user.email
		stored.save()
	except User.DoesNotExist:
		user.save()
		stored = user
	stored.storePassword(password)
	_currentUser.user = stored
	return stored

_currentUser = threading.local()

def current_user():
	return _currentUser.user if hasattr(_currentUser, "user") else None
	
def set_current_user(user):
	_currentUser.user = user

providers = []
print >>sys.stderr, "Loading auth modules..."
for conf in config.AUTH:
	provider = None #make eclipse shut up
	exec("import %s_provider as provider" % conf["PROVIDER"]) #pylint: disable-msg=W0122
	prov = provider.init(**(conf["OPTIONS"]))
	prov.name = conf["NAME"]
	providers.append(prov)
	print >>sys.stderr, " - %s (%s)" % (conf["NAME"], conf["PROVIDER"])
if not providers:
	print >>sys.stderr, "Warning: No authentication modules configured."