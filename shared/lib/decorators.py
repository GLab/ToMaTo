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

import time

"""
Synchronization decorator
  This decorator can be used to synchronize method calls. Synchronization is relative to 
  some kind of lock. Before each function call the acquire method of the lock is called,
  and after the function call the release method is called regardless of exceptions.

Example:
  @synchronized(threading.Lock())
  def critical():
    ...critical_block...
"""
def synchronized(lock):
	def wrap(fn):
		def call(*args, **kwargs):
			lock.acquire()
			try:
				return fn(*args, **kwargs)
			finally:
				lock.release()
		call.__name__ = fn.__name__
		call.__doc__ = fn.__doc__
		call.__dict__.update(fn.__dict__)
		return call
	return wrap


#atexit.register can be used directly


"""
Detach decorator
  This decorator can be used to run functions in parallell to normal execution.
  For each function call a new thread is created to execute the function call.
  
Example:
  @detached
  def long_function():
    ...long_function...
"""
def detached(fn):
	from thread import start_new_thread
	def call(*args, **kwargs):
		return start_new_thread(fn, args, kwargs)
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call


"""
Every decorator
  This decorator can be used to run a method periodically. The period can be given as a
  combination as seconds, millis, minutes, hours and days as kwargs. The method will be
  repeated until the main thread exits.
  
Example:
  @every(minutes=30, hours=1)
  def housekeeping():
    ...some_periodic_task...
"""
def every(seconds=0, millis=0, minutes=0, hours=0, days=0):
	from thread import start_new_thread
	from time import sleep
	import atexit
	period = millis / 1000 + seconds + 60 * ( minutes + 60 * ( hours + 24 * days ) ) 
	def wrap(fn):
		running = True
		def run():
			while running:
				sleep(period)
				fn()
		def stop():
			running = False
		start_new_thread(run,())
		atexit.register(stop)
		return fn
	return wrap


"""
Profile decorator
  This decorator can be used to profile a method. The output filename can be given
  as a parameter. If the additional appendDate is given, the current date at the time
  of execution is appended to the filename.
  
Example:
  @profile(outfile)
  def profileme():
    ...some_cpu_intensive_task...
"""
def profile(out, appendDate=False):
	try:
		import cProfile as profile #@UnusedImport
	except:
		import profile #@Reimport
	if appendDate:
		import datetime
	def wrap(fn):
		def call(*args, **kwargs):
			ldict = locals().copy()
			ldict.update({"fn": fn, "args": args, "kwargs": kwargs})
			if appendDate:
				out = "%s-%s" % (out, datetime.datetime.now().isoformat())
			profile.runctx("rtn = fn(*args, **kwargs)", globals(), ldict, out)
			return ldict["rtn"]
		call.__name__ = fn.__name__
		call.__doc__ = fn.__doc__
		call.__dict__.update(fn.__dict__)
		return call
	return wrap


def handleErrors(handle):
	def wrap(fn):
		def call(*args, **kwargs):
			try:
				return fn(*args, **kwargs)
			except Exception, exc:
				handle(exc)
		call.__name__ = fn.__name__
		call.__doc__ = fn.__doc__
		call.__dict__.update(fn.__dict__)
		return call
	return wrap

def xmlRpcSafe(fn):
	def call(*args, **kwargs):
		res = fn(*args, **kwargs)
		assert util.xml_rpc_safe(res), "Output is not XML-RPC safe: %s" % res
		return res
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call

def xmlRpcSanitize(fn):
	def call(*args, **kwargs):
		return util.xml_rpc_sanitize(fn(*args, **kwargs))
	call.__name__ = fn.__name__
	call.__doc__ = fn.__doc__
	call.__dict__.update(fn.__dict__)
	return call

"""
RetryOnError
  This decorator can be used to retry a method call on error.
  
Example:
  @retryOnError()
  def canFail():
    ...
"""
def retryOnError(errorFilter=None, maxRetries=5, waitBetween=0.5, waitIncrease=2.0, randomWait=True):
	from time import sleep
	from random import random
	def wrap(fn):
		def call(*args, **kwargs):
			retries = maxRetries
			wait = waitBetween
			while True:
				try:
					return fn(*args, **kwargs)
				except Exception, exc:
					if not retries:
						raise 
					if callable(errorFilter) and not errorFilter(exc):
						raise
				retries -= 1
				if wait:
					t = wait
					if randomWait:
						t *= 0.5 + random()
					sleep(t)
					if waitIncrease:
						wait *= waitIncrease
		call.__name__ = fn.__name__
		call.__doc__ = fn.__doc__
		call.__dict__.update(fn.__dict__)
		return call
	return wrap

import util