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

import time, sys

class Cache:
	def __init__(self, maxSize=100, timeout=None):
		self._values={}
		self._order=[]
		self._maxSize=maxSize
		self._timeout=timeout
	def __getitem__(self, key):
		(value, timeout) = self._values[key] #This will trigger IndexError on purpose
		if timeout >= time.time():
			return value
		else:
			raise IndexError("entry has timed out")
	def __setitem__(self, key, value):
		if len(self._order) >= self._maxSize:
			delkey = self._order.pop(0)
			del self._values[delkey]
		self._order.append(key)
		timeout = (time.time() + self._timeout) if self._timeout else sys.maxint
		self._values[key] = (value, timeout)
	def __delitem__(self, key):
		del self._values[key] #This will trigger IndexError on purpose
		self._order.remove(key)
	def __contains__(self, key):
		return key in self._values
	def clear(self):
		self._values = {}
		self._order = []
	
class CachedMethod:
	def __init__(self, fn, cache):
		self._fn = fn
		self._cache = cache
	def __call__(self, *args, **kwargs):
		key = (tuple(args), tuple(kwargs.items()))
		if key in self._cache:
			try:
				return self._cache[key]
			except IndexError:
				pass
		value = self._fn(*args, **kwargs)
		self._cache[key] = value
		return value
	def invalidate(self):
		self._cache.clear()	
	
def cached(timeout=None, cache=None, maxSize=100):
	def wrap(fn):
		_cache = cache if cache else Cache(timeout=timeout, maxSize=maxSize)
		call = CachedMethod(fn, _cache)
		call.__name__ = fn.__name__
		call.__doc__ = fn.__doc__
		call.__dict__.update(fn.__dict__)
		return call
	return wrap