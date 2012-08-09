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

from tomato import fault
from tomato.lib import db, attributes, util
from tomato.lib.decorators import *

TYPES = ["template", "external_network"]

class Resource(db.ChangesetMixin, db.ReloadMixin, attributes.Mixin, models.Model):
    type = models.CharField(max_length=20, validators=[db.nameValidator], choices=[(t, t) for t in TYPES])
    attrs = db.JSONField()
    
    class Meta:
        pass

    def init(self, attrs):
        self.attrs = attrs
        self.save()
        
    def upcast(self):
        try:
            return getattr(self, self.type)
        except:
            pass
        fault.raise_("Failed to cast resource #%d to type %s" % (self.id, self.type))
    
    def info(self):
        return {
            "id": self.id,
            "type": self.type,
            "attrs": self.attrs,
        }
    
def get(id_, **kwargs):
    try:
        el = Resource.objects.get(id=id_, **kwargs)
        return el.upcast()
    except:
        return None

def getAll(**kwargs):
    return (res.upcast() for res in Resource.objects.filter(**kwargs))