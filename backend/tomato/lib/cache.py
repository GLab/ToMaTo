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

import time, sys, threading, thread

class CacheUpdater:
	caches = []
	lock = threading.RLock()
	def add(self, cache):
		with self.lock:
			self.caches.append(cache)
	def remove(self, cache):
		with self.lock:
			self.caches.remove(cache)
	def start_updating(self, interval):
		from .. import scheduler
		scheduler.scheduleRepeated(interval, self.update_all, immediate=False)
	def update_all(self):
		with self.lock:
			for cache in self.caches:
				thread.start_new_thread(cache.update_all)
cache_updater = None

class Cache:
	def __init__(self, fn, maxSize=100, timeout=None, autoupdate=False):
		self._values={} #{key:{value, timeout, auto_timeout, args, kwargs}}
		self._order=[]  #[key]
		self._maxSize=maxSize
		self._timeout=timeout
		self._fn = fn
		self._lock = threading.RLock()
		self._autoupdate = autoupdate
		self._autoupdate_registered = not self._autoupdate # registration for auto-updates will be checked when a value is set.
															# this is false iff this cache needs to be added to the auto updater.
	@staticmethod
	def getKey(args, kwargs):
		return (tuple(args), tuple(kwargs.items()))
	def get(self, args, kwargs):
		with self._lock:
			key = Cache.getKey(args, kwargs)
			if (not key in self._values) or (self._values[key]['timeout'] <= time.time()):
				self.update(args, kwargs)
			return self._values[Cache.getKey(args, kwargs)]['value']
	def update(self, args, kwargs):
		with self._lock:
			value = self._fn(*args, **kwargs)
			self.set(args, kwargs, value)
	def set(self, args, kwargs, value):
		with self._lock:
			key = Cache.getKey(args, kwargs)
			
			#clear oldest entry if cache is full
			if len(self._order) >= self._maxSize:
				delkey = self._order.pop(0)
				del self._values[delkey]
				
			#maintain order of caching
			if key in self._values:
				self._order.remove(key)
			self._order.append(key)
			
			#save value
			timeout = (time.time() + self._timeout) if self._timeout else sys.maxint
			auto_timeout = timeout - 0.25*self._timeout if self._timeout else sys.maxint #auto-refresh triggers after 3/4 timeout
			self._values[key] = {'value':value,
								 'timeout':timeout,
								 'auto_timeout':auto_timeout,
								 'args':args,
								 'kwargs':kwargs}
		if not self._autoupdate_registered:
			if cache_updater is not None:
				cache_updater.add(self)
				self._autoupdate_registered = True
	def remove(self, args, kwargs):
		with self._lock:
			key = Cache.getKey(args, kwargs)
			del self._values[key]
			self._order.remove(key)
	def contains(self, args, kwargs):
		with self._lock:
			return Cache.getKey(args, kwargs) in self._values
	def clear(self):
		with self._lock:
			self._values = {}
			self._order = {}
	def update_all(self):
		if self._autoupdate:
			for key in list(self._order): #since maxsize is bounded, this is not a scaling problem.
				with self._lock: #release the lock between all cycles to allow other threads to step in between two iterations.
								#this function can only change the order of entries, but does not delete any.
					res = self._values[key]
					if res['auto_timeout'] <= time.time():
						self.update(res['args'], res['kwargs'])
		
		
	
class CachedMethod:
	def __init__(self, fn, cache):
		self._fn = fn
		self._cache = cache
	def __call__(self, *args, **kwargs):
		return self._cache.get(args, kwargs)
	def invalidate(self):
		self._cache.clear()	
	
def cached(timeout=None, cache=None, maxSize=100, autoupdate=False):
	def wrap(fn):
		_cache = cache if cache else Cache(fn=fn, timeout=timeout, maxSize=maxSize, autoupdate=autoupdate)
		call = CachedMethod(fn, _cache)
		call.__name__ = fn.__name__
		call.__doc__ = fn.__doc__
		call.__dict__.update(fn.__dict__)
		return call
	return wrap

def init():
	cache_updater = CacheUpdater()
	cache_updater.start_updating(5*60)
	