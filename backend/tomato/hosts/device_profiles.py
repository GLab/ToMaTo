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
	
	def configure(self, attributes):
		self.attrs = attributes
		self.save()
		
	def setDefault(self):
		DeviceProfile.objects.filter(type=self.type).update(default=False) # pylint: disable-msg=E1101
		self.default=True
		self.save()

def getAll(type_=None):
	prfls = DeviceProfile.objects.all() # pylint: disable-msg=E1101
	if type_:
		prfls = prfls.filter(type=type_)
	return prfls

def findName(type_, name):
	try:
		prfl = DeviceProfile.objects.get(type=type_, name=name) # pylint: disable-msg=E1101
		return prfl.name
	except: #pylint: disable-msg=W0702
		return getDefault(type_)

def getMap(auth):
	map = {}
	for prfl in getAll():
		if not prfl.type in map:
			map[prfl.type] = []
		map[prfl.type].append(prfl.toDict(auth)) 
	return map

def get(type_, name):
	return DeviceProfile.objects.get(type=type_, name=name) # pylint: disable-msg=E1101

def add(type_, name, attributes):
	prfl = DeviceProfile.objects.create(name=name, type=type_) # pylint: disable-msg=E1101
	return prfl.configure(attributes)

def change(type_, name, attributes):
	prfl = get(type_, name)
	return prfl.configure(attributes)
	
def remove(type_, name):
	DeviceProfile.objects.filter(type=type_, name=name).delete() # pylint: disable-msg=E1101
	
def getDefault(type_):
	prfls = DeviceProfile.objects.filter(type=type_, default=True) # pylint: disable-msg=E1101
	if prfls.count() >= 1:
		return prfls[0].name
	else:
		return None

# keep internal imports at the bottom to avoid dependency problems
from tomato.hosts import getAll as getAllHosts
from tomato import fault
from tomato.lib import tasks
from tomato.hosts import ClusterState