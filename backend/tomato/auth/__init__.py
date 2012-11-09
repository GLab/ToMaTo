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

import time, datetime, crypt, string, random, sys, threading
from django.db import models
from ..lib import attributes, db, logging, util #@UnresolvedImport
from .. import config, fault, currentUser

class Flags:
    Admin = "admin" # Can modify all accounts
    Debug = "debug" # Can see everything
    HostsManager = "hosts_manager" # Can manage all hosts and sites
    GlobalOwner = "global_owner" # Owner for every topology
    GlobalManager = "global_manager" # Manager for every topology
    GlobalUser = "global_user" # User for every topology    
    NoTopologyCreate = "no_topology_create" # Restriction on topology_create
    OverQuota = "over_quota" # Restriction on actions start, prepare and upload_grant
    NewAccount = "new_account" # Account is new, just a tag

RESTRICTED_ATTRS = ["flags", "password_time", "password", "origin", "name", "last_login"]

class User(attributes.Mixin, models.Model):
    name = models.CharField(max_length=255)
    origin = models.CharField(max_length=50)
    attrs = db.JSONField()
    password = models.CharField(max_length=250, null=True)
    password_time = models.FloatField(null=True)
    last_login = models.FloatField(default=time.time())
    
    realname = attributes.attribute("realname", str)
    affiliation = attributes.attribute("affiliation", str)
    email = attributes.attribute("email", str)
    flags = attributes.attribute("flags", list, [])

    class Meta:
        db_table = "tomato_user"
        app_label = 'tomato'
        unique_together = (("name", "origin"),)
        ordering=["name", "origin"]

    @classmethod    
    def create(cls, name, **kwargs):
        user = User(name=name)
        user.attrs = kwargs
        user.last_login = time.time()
        return user
    
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

    def modify(self, attrs):
        logging.logMessage("modify", category="user", name=self.name, origin=self.origin, attrs=attrs)    
        for key, value in attrs.iteritems():
            fault.check(not key in RESTRICTED_ATTRS or currentUser().hasFlag(Flags.Admin), "No permission to change attribute %s", key)
            self.attrs[key] = value
        self.save()

    def info(self):
        info = {
            "name": self.name,
            "origin": self.origin,
            "id": "%s@%s" % (self.name, self.origin) 
        }
        info.update(self.attrs)
        return info
        
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
    def register(self, username, password, attrs):
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
        fault.raise_("Multiple users with that name exist, specify origin", code=fault.USER_ERROR)

def getAllUsers():
    return User.objects.all()

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

def register(username, password, attrs={}, provider=""):
    for prov in providers:
        if not prov.getName() == provider:
            continue
        fault.check(prov.canRegister(), "Provider can not register users")
        return prov.register(username, password, attrs)
    fault.raise_("No provider named %s" % provider, fault.USER_ERROR)

def changePassword(password):
    user = currentUser()
    for prov in providers:
        if not prov.getName() == user.origin:
            continue
        fault.check(prov.canChangePassword(), "Provider can not change password")
        prov.changePassword(user.name, password)
        user.storePassword(password)

providers = []

task = util.RepeatedTimer(300, cleanup) #every 5 minutes

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