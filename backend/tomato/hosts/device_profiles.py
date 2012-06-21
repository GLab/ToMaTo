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

from tomato import attributes
from tomato.lib import db, util

class DeviceProfile(attributes.Mixin, models.Model):
	name = models.CharField(max_length=100, validators=[db.nameValidator])
	type = models.CharField(max_length=12, validators=[db.nameValidator])
	restricted = models.BooleanField(default=False)
	default = models.BooleanField(default=False)
	attrs = db.JSONField(default={})
			
	class Meta:
		db_table = "device_profile"
		app_label = 'tomato'
		unique_together = (("name", "type"),)
		ordering=["type", "name"]

	def init(self, name, type_, restricted=False, default=False):
		self.name = name
		self.type = type_
		self.restricted = restricted
		self.default = default
		self.save()

	def __unicode__(self):
		return "DeviceProfile(type=%s,name=%s,restricted=%s)" %(self.type, self.name, self.restricted)
			
	def toDict(self, auth=False):
		"""
		Prepares a device profile for serialization.
			
		@return: a dict containing information about the device profile
		@rtype: dict
		"""
		res = {"name": self.name, "type": self.type, "default": self.default,
			"restricted": self.restricted, "attrs": self.attrs}
		return res

from tomato import fault