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

from django.db import models
import random, sys

from tomato import fault
from tomato.elements import Element
from tomato.lib import db, attributes, util
from tomato.lib.decorators import *

TYPES = {}

class Resource(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
    type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES])
    attrs = db.JSONField()
    numStart = attributes.attribute("num_start", int)
    numCount = attributes.attribute("num_count", int)
    
    class Meta:
        pass

    def init(self, attrs={}):
        self.attrs = {}
        self.save()
        self.modify(attrs)
        
    def getInstanceRange(self):
        fault.check(self.numStart and self.numCount, "This resource can not have any instances", code=fault.INTERNAL_ERROR)
        return xrange(self.numStart, self.numStart + self.numCount)
        
    def upcast(self):
        if not self.type in TYPES:
            return self
        try:
            return getattr(self, self.type)
        except:
            pass
        fault.raise_("Failed to cast resource #%d to type %s" % (self.id, self.type), code=fault.INTERNAL_ERROR)
    
    def modify(self, attrs):
        for key, value in attrs.iteritems():
            if hasattr(self, "modify_%s" % key):
                getattr(self, "modify_%s" % key)(value)
            else:
                self.attrs[key] = value
        self.save()
    
    def modify_num_start(self, val):
        self.num_start = val
    
    def modify_num_count(self, val):
        self.num_count = val

    def remove(self):
        self.delete()    
    
    def info(self):
        return {
            "id": self.id,
            "type": self.type,
            "attrs": self.attrs,
        }
    
class ResourceInstance(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
    type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES])
    num = models.IntegerField()
    owner = models.ForeignKey(Element, null=False)
    attrs = db.JSONField()
    
    class Meta:
        unique_together = (("num", "type"),)

    def init(self, type, num, owner, attrs={}):
        self.type = type
        self.num = num
        self.owner = owner
        self.attrs = attrs
        self.save()

def take(type_, owner):
    res = getByType(type_)
    fault.check(res, "Multiple or none resources of type %s found", type_, fault.INTERNAL_ERROR)
    range_ = res.getInstanceRange()
    for try_ in xrange(0, 100): 
        num = random.choice(range_)
        try:
            ResourceInstance.objects.get(type=type_, num=num)
            continue
        except ResourceInstance.DoesNotExist:
            pass
        try:
            instance = ResourceInstance()
            instance.init(type_, num, owner)
            return num
        except:
            pass
    fault.raise_("Failed to obtain resource of type %s after %d tries" % (type_, try_), code=fault.INTERNAL_ERROR)

def give(type_, num, owner):
    instance = ResourceInstance.objects.get(type=type_, num=num, owner=owner)
    instance.delete()

def get(id_, **kwargs):
    try:
        el = Resource.objects.get(id=id_, **kwargs)
        return el.upcast()
    except:
        return None

def getByType(type_, **kwargs):
    try:
        el = Resource.objects.get(type=type_, **kwargs)
        return el.upcast()
    except:
        return None

def getAll(**kwargs):
    return (res.upcast() for res in Resource.objects.filter(**kwargs))

def _addResourceRange(type_, start, count):
    return create(type_, {"num_start": start, "num_count": count})

def create(type_, attrs={}):
    if type_ in TYPES:
        res = TYPES[type_]()
    else:
        res = Resource(type=type_)
    res.init(attrs)
    res.save()
    return res

def init():
    if not getByType("vmid"):
        print >>sys.stderr, "Adding default resource entry for vmid"
        _addResourceRange("vmid", 1000, 1000)
    if not getByType("port"):
        print >>sys.stderr, "Adding default resource entry for port"
        _addResourceRange("port", 6000, 1000)
