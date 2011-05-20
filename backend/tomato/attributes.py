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

class AttributeSet(models.Model):
	def clean(self):
		for r in self.attributeentry_set.all(): # pylint: disable-msg=E1101
			r.delete()
	def set(self, name, value):
		entr = self.get_entry(name)
		if not entr:
			if value is None:
				return
			entr = AttributeEntry(attribute_set=self, name=name, value=value)
			entr.save()
			self.attributeentry_set.add(entr) # pylint: disable-msg=E1101
		else:
			if value is None:
				entr.delete();
				return
			entr.value = value
			entr.save()
		self.save()
	def get_entry(self, name):
		if len(self.attributeentry_set.filter(name=name)) == 0: # pylint: disable-msg=E1101
			return None
		else:
			return self.attributeentry_set.get(name=name) # pylint: disable-msg=E1101
	def get(self, name):
		entr = self.get_entry(name)
		return entr.value if entr else None
	
	#dict methods
	def __len__(self):
		return len(self.attributeentry_set.all())
	def __getitem__(self, key):
		return self.get(key)
	def __setitem__(self, key, value):
		self.set(key, value)
	def __delitem__(self, key):
		entr = self.get_entry(key)
		if not entr:
			#raise KeyError("no such key: %s" % key)
			return
		entr.delete()
	def __iter__(self):
		return (entr.name for entr in self.attributeentry_set.all())
	def iterkeys(self):
		return self.__iter__()
	def items(self):
		return ((entr.name, entr.value) for entr in self.attributeentry_set.all())
	def __contains__(self, key):
		return not self.get(key) is None

class AttributeEntry(models.Model):
	attribute_set = models.ForeignKey(AttributeSet)
	name = models.CharField(max_length=250)
	value = models.CharField(max_length=250, null=True)

def create():
	attr = AttributeSet()
	attr.save()
	return attr