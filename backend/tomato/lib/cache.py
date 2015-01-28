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
	def add(self, cache):
		self.caches.append(cache)
	def remove(self, cache):
		self.caches.remove(cache)
	def start_updating(self, interval):
		from .. import scheduler
		scheduler.scheduleRepeated(interval, self.update_all, immediate=False)
	def update_all(self):
		for cache in list(self.caches):
			cache.update_all()
cache_updater = None

class Cache:
	def __init__(self, fn=None, maxSize=100, timeout=None, autoupdate=False):
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
		key = Cache.getKey(args, kwargs)
		with self._lock:
			if (not key in self._values) or (self._values[key]['timeout'] <= time.time()):
				self.update(args, kwargs)
			return self._values[Cache.getKey(args, kwargs)]['value']
	def update(self, args, kwargs):
		calltime = time.time()
		value = self._fn(*args, **kwargs) #there may be concurrent method calls here. set() will resolve this.
		self.set(args, kwargs, value, calltime=calltime)
	def set(self, args, kwargs, value, calltime=None):
		key = Cache.getKey(args, kwargs)
		if calltime is None:
			calltime = time.time()
		with self._lock:
			
			timeout = (calltime + self._timeout) if self._timeout else sys.maxint
			auto_timeout = timeout - 0.25*self._timeout if self._timeout else sys.maxint #auto-refresh triggers after 3/4 timeout
			
			#check whether another thread has accessed this function concurrently (may happen in update). If yes, do not save this.
			if key in self._values:
				if self._values[key]['timeout'] > timeout:
					return
			
			#clear oldest entry if cache is full
			if len(self._order) >= self._maxSize:
				delkey = self._order.pop(0)
				del self._values[delkey]
				
			#make sure that this key is not in _order (it may only be once in there)
			if key in self._values:
				self._order.remove(key)
				
			#save
			self._order.append(key)
			self._values[key] = {'value':value,
								 'timeout':timeout,
								 'auto_timeout':auto_timeout,
								 'args':args,
								 'kwargs':kwargs}
			
			#finally, register this cache for auto-update if needed.
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
			self._order = []
	def update_all(self):
		if self._autoupdate:
			for key in list(self._order): #since maxsize is bounded, this is not a scaling problem.
				with self._lock: #release the lock between all cycles to allow other threads to step in between two iterations.
								#    This function can only change the order of entries, but does not delete any.
								# Concurrent calls may remove the first entries of the list. In this case, this function should ignore these entries.
								#    However, there is only a really slight chance that this happens, and it doesn't lead to inconsistency.
								#	 This only means there is no guarantee that the key is still in the list when entering the lock.
								#        Conclusion: only do something if the key is still cached.
					if key in self._values:
						res = self._values[key]
						if res['auto_timeout'] <= time.time():
							self.update(res['args'], res['kwargs'])
		
		
	
class CachedMethod:
	def __init__(self, cache):
		self._cache = cache
	def __call__(self, *args, **kwargs):
		return self._cache.get(args, kwargs)
	def invalidate(self):
		self._cache.clear()	
	
def cached(timeout=None, maxSize=100, autoupdate=False):
	if maxSize is None:
		maxSize = 10000
	def wrap(fn):
		_cache = Cache(fn=fn, timeout=timeout, maxSize=maxSize, autoupdate=autoupdate)
		call = CachedMethod(_cache)
		call.__name__ = fn.__name__
		call.__doc__ = fn.__doc__
		call.__dict__.update(fn.__dict__)
		return call
	return wrap

def init():
	global cache_updater
	cache_updater = CacheUpdater()
	cache_updater.start_updating(5*60) #refresh every five minutes. For most caches, this usually means iterating through a list without doing anything.
	