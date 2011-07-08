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

class State(): #pylint: disable-msg=W0232
	"""
	The state of the element, this is an assigned value. The states are considered to be in order:
	created -> prepared -> started
	created		the element has been created but not prepared
	prepared	all devices have been prepared
	started		the element has been prepared and is currently up and running
	"""
	CREATED="created"
	PREPARED="prepared"
	STARTED="started"

class ObjectPreferences:
	def __init__(self, exclusive=False):
		self.exclusive = exclusive
		self.objects = []
		self.values = []
	def add(self, obj, value=1.0):
		try:
			index = self.objects.index(obj)
			self.values[index]+=value
		except:
			self.objects.append(obj)
			self.values.append(value)
	def remove(self, obj):
		try:
			index = self.objects.index(obj)
			del self.objects[index]
			del self.values[index]
		except:
			pass
	def getValue(self, obj):
		try:
			index = self.objects.index(obj)
			return self.values[index]
		except:
			return None
	def contains(self, obj):
		return not (self.getValue(obj) is None)
	def combine(self, other):
		if other.exclusive and not self.exclusive:
			return other.combine(self)
		res = ObjectPreferences(self.exclusive or other.exclusive)
		if self.exclusive:
			for o in self.objects:
				val = self.getValue(o)
				oval = other.getValue(o)
				if not (oval is None and other.exclusive):
					res.add(o, (oval + val) if oval else val)
		else:
			for o in self.objects:
				res.add(o, self.getValue(o))
			for o in other.objects:
				res.add(o, other.getValue(o))
		return res
	def best(self):
		max_val = None
		best = None
		i = 0
		while i < len(self.values):
			if max_val is None or max_val < self.values[i]:
				max_val = self.values[i]
				best = self.objects[i]
			i=i+1
		return best
	def __str__(self):
		strs = []
		i=0
		while i < len(self.values):
			strs.append("%s: %s" %(self.objects[i], self.values[i]))
			i=i+1
		type = "exclusive" if self.exclusive else "hint"
		return type + ":{" + (", ".join(strs)) + "}"