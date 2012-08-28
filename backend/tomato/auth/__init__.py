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

import time, atexit, datetime, crypt, string, random, sys, threading
from django.db import models
from tomato.lib import attributes, db #@UnresolvedImport
from tomato import config

class User(attributes.Mixin, models.Model):
    name = models.CharField(max_length=255)
    origin = models.CharField(max_length=50)
    attrs = db.JSONField()
    password = models.CharField(max_length=250, null=True)
    password_time = models.DateTimeField(null=True)
    
    realname = attributes.attribute("realname", str)
    email = attributes.attribute("email", str)
    restrictions = attributes.attribute("restrictions", list, [])

    class Meta:
        db_table = "tomato_user"
        app_label = 'tomato'
        unique_together = (("name", "origin"),)
        ordering=["name", "origin"]
    
    def _saveAttributes(self):
        pass #disable automatic attribute saving
    
    def checkPassword(self, password):
        return self.password == crypt.crypt(password, self.password)

    def storePassword(self, password):
        saltchars = string.ascii_letters + string.digits + './'
        salt = "$1$"
        salt += ''.join([ random.choice(saltchars) for _ in range(8) ])
        self.password = crypt.crypt(password, salt)
        self.password_time = datetime.datetime.now()
        self.save()
    
    def hasRestriction(self, restriction):
        return restriction in self.restrictions
    
    def addRestriction(self, restriction):
        if self.hasRestriction(restriction):
            return
        self.restrictions.append(restriction)
        self.save()
        
    def removeRestriction(self, restriction):
        if not self.hasRestriction(restriction):
            return
        self.restrictions.remove(restriction)
        self.save()
        
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
            print "Successfull login: %s" % user
            return user
    print "Failed login: %s" % username
    return None

def login(username, password):
    for user in User.objects.filter(name = username):
        if user.password and user.checkPassword(password):
            return user
    user = provider_login(username, password)
    if not user:
        return None
    try:
        stored = User.objects.get(name=user.name, origin=user.origin)
        stored.is_admin = user.is_admin
        stored.save()
    except User.DoesNotExist:
        user.save()
        stored = user
    stored.storePassword(password)
    return stored

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