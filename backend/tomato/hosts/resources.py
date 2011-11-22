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

import random, itertools

from tomato import fault
from tomato.lib import db

from tomato.hosts import Host

TYPES = ["vmid", "ifb", "bridge", "port"]

def _ownerTypeMap():
	import tomato.models as m
	return {"D": m.Device, "C": m.Connector, "c": m.Connection, "i": m.Interface}
	

def lookupOwner(type, id):
	try:
		return _ownerTypeMap().get(type).objects.get(id=id)
	except:
		return None
		
def ownerTuple(obj):
	for n, t in _ownerTypeMap().iteritems():
		if isinstance(obj, t):
			return (n, obj.id)
	raise fault.new("Invalid resource owner type: %s" % obj)

def _log(msg):
	fault.log_info("Resource problem", msg)

class ResourcePoolEmpty(Exception):
	pass

class ResourcePool(models.Model):
	host = models.ForeignKey(Host)
	type = models.CharField(max_length=10, choices=((t, t) for t in TYPES))
	first_num = models.IntegerField()
	num_count = models.IntegerField()

	class Meta:
		db_table = "tomato_resourcepool"	
		app_label = 'tomato'
		unique_together = (("host", "type"),)

	def get(self, owner, slot):
		owner_type, owner_id = ownerTuple(owner)
		try:
			return ResourceEntry.objects.get(pool=self, owner_type=owner_type, owner_id=owner_id, slot=slot)
		except ResourceEntry.MultipleObjectsReturned:
			for res in ResourceEntry.objects.filter(pool=self, owner_type=owner_type, owner_id=owner_id, slot=slot)[1:]:
				res.delete()
			return self.get(owner, slot)
		except ResourceEntry.DoesNotExist:
			return None

	def totalResources(self):
		return self.num_count
			
	def availableResources(self):
		return self.totalResources() - self.resourceentry_set.count()

	def take(self, owner, slot, num=None):
		owner_type, owner_id = ownerTuple(owner)
		old = self.get(owner, slot)
		if old:
			_log("owner %s of %s requested same resources again" % (owner, old) )
			return old
		if not self.availableResources():
			raise ResourcePoolEmpty()
		start = num if not num is None else random.choice(xrange(self.first_num, self.first_num+self.num_count))
		for num in itertools.chain(xrange(start, self.first_num+self.num_count), xrange(self.first_num, start)):
			assert self.first_num <= num <= self.first_num+self.num_count
			try:
				ResourceEntry.objects.get(pool=self, num=num)
				#do not rely on unique constraint
			except ResourceEntry.MultipleObjectsReturned:
				usages = ResourceEntry.objects.filter(pool=self, num=num)
				_log("Duplicate usage detected: %s" % usages)
			except ResourceEntry.DoesNotExist:
				try:
					res = ResourceEntry.objects.create(pool=self, num=num, owner_type=owner_type, owner_id=owner_id, slot=slot)
					if db.transaction.is_dirty():
						db.transaction.commit()
					return res
				except Exception:
					import traceback
					traceback.print_exc()
					pass
		_log("%s was not empty but has no free slots left" % self)
		raise ResourcePoolEmpty()
		
	def give(self, owner, slot):
		res = self.get(owner, slot)
		if res:
			res.delete()
		else:
			_log("%s returned a %s resource to %s that it didnt have" % (owner, slot, self))
					
	def checkOwners(self):
		for r in self.resourceentry_set.all():
			if not r.getOwner():
				_log("owner of %s does not exist" % r)
				r.delete()
						
	def __str__(self):
		return "ResourcePool(%s, %s)" % (self.host.name, self.type)

class ResourceEntry(models.Model):
	pool = models.ForeignKey(ResourcePool)
	num = models.IntegerField()
	owner_type = models.CharField(max_length=10)
	owner_id = models.IntegerField()
	slot = models.CharField(max_length=10)
	
	class Meta:
		db_table = "tomato_resourceentry"	
		app_label = 'tomato'
		unique_together = (("pool", "num"),("owner_type", "owner_id", "slot"))

	def getType(self):
		return self.pool.type
			
	def getHost(self):
		return self.pool.host

	def checkOwner(self, obj):
		return ownerTuple(obj) == (self.owner_type, self.owner_id)

	def getOwner(self):
		return lookupOwner(self.owner_type, self.owner_id)
		
	def __str__(self):
		return "Resource(%d of %s@%s, owner=%s.%d, slot=%s)" % (self.num, self.getType(), self.getHost().name, self.owner_type, self.owner_id, self.slot)
	
def createPool(host, type, first_num, num_count):
	pool = ResourcePool.objects.create(host=host, type=type, first_num=first_num, num_count=num_count)
	host.resourcepool_set.add(pool)
	
def getPool(host, type):
	try:
		return ResourcePool.objects.get(host=host, type=type)
	except ResourcePool.DoesNotExist:
		return None
	
def take(host, type, owner, slot, num=None):
	assert host, "No host given"
	assert type in TYPES, "Invalid type"
	pool = getPool(host, type)
	if not pool:
		raise ResourcePoolEmpty()
	return pool.take(owner, slot, num)
	
def give(owner, slot):
	res = get(owner, slot)
	if res:
		res.pool.give(owner, slot)

def get(owner, slot, attr=None, assign=True, save=True):
	owner_type, owner_id = ownerTuple(owner)
	if attr and hasattr(owner, attr):
		res = getattr(owner, attr)
		if res and isinstance(attr, ResourceEntry):
			if res.checkOwner(owner):
				return res
			elif assign:
				setattr(owner, attr, None)
				if save:
					owner.save()
	try:
		res = ResourceEntry.objects.get(owner_type=owner_type, owner_id=owner_id, slot=slot)
		if attr and hasattr(owner, attr):
			setattr(owner, attr, None)
			if save:
				owner.save()
		return res
	except ResourceEntry.DoesNotExist:
		return None
		
def getAll(owner):
	owner_type, owner_id = ownerTuple(owner)
	try:
		return ResourceEntry.objects.filter(owner_type=owner_type, owner_id=owner_id)
	except ResourceEntry.DoesNotExist:
		return None