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
from .. import resources
from ..lib import attributes #@UnresolvedImport
from ..lib.error import UserError, InternalError

TECHS = ["kvmqm", "openvz", "repy"]
DEFAULTS = {
	"kvmqm": {"ram": 512, "cpus": 1, "diskspace": 10240},
	"openvz": {"ram": 512, "diskspace": 10240},
	"repy": {"ram": 50, "cpus": 0.25},
}

class Profile(resources.Resource):
	tech = models.CharField(max_length=20)
	name = models.CharField(max_length=50)
	preference = models.IntegerField(default=0)
	label = attributes.attribute("label", str)
	restricted = attributes.attribute("restricted", bool, False)
	
	TYPE = "profile"

	class Meta:
		db_table = "tomato_profile"
		app_label = 'tomato'
	
	def init(self, *args, **kwargs):
		self.type = self.TYPE
		attrs = args[0]
		for attr in ["name", "tech"]:
			UserError.check(attr in attrs, code=UserError.INVALID_CONFIGURATION, message="Profile needs attribute",
				data={"attribute": attr})
		resources.Resource.init(self, *args, **kwargs)
				
	def upcast(self):
		return self
	
	def modify_name(self, val):
		self.name = val

	def modify_tech(self, val):
		UserError.check(val in TECHS, code=UserError.INVALID_VALUE, message="Unsupported profile tech", data={"value": val})
		self.tech = val
		
	def modify_preference(self, val):
		self.preference = val

	def info(self):
		info = resources.Resource.info(self)
		info["attrs"]["name"] = self.name
		info["attrs"]["tech"] = self.tech
		info["attrs"]["preference"] = self.preference
		return info

def get(tech, name):
	try:
		return Profile.objects.get(tech=tech, name=name)
	except:
		return None
	
def getPreferred(tech):
	prfls = Profile.objects.filter(tech=tech).order_by("-preference")
	InternalError.check(prfls, code=InternalError.CONFIGURATION_ERROR, message="No profile for this type registered", data={"tech": tech})
	return prfls[0]

resources.TYPES[Profile.TYPE] = Profile