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

import threading, thread, traceback, time, xmlrpclib, datetime
from decorators import xmlRpcSafe

class RepeatedTimer(threading.Thread):
	def __init__(self, timeout, func, *args, **kwargs):
		self.timeout = timeout
		self.func = func
		self.args = args
		self.kwargs = kwargs
		threading.Thread.__init__(self)
		self.stopped = threading.Event()
		self.stopped_confirm = threading.Event()
		self.daemon = True
	def run(self):
		while not self.stopped.isSet():
			try:
				self.stopped.wait(self.timeout)
			except: #pylint: disable-msg=W0702
				self.stopped_confirm.set()
				return
			if not self.stopped.isSet():
				try:
					self.func(*self.args, **self.kwargs)
				except Exception, exc: #pylint: disable-msg=W0703
					from .. import fault
					fault.errors_add(exc, traceback.format_exc())
		self.stopped_confirm.set()
	def stop(self):
		self.stopped.set()
		try:
			self.stopped_confirm.wait()
		except:
			pass

def print_except_helper(func, args, kwargs):
	try:
		return func(*args, **kwargs) #pylint: disable-msg=W0142
	except Exception, exc: #pylint: disable-msg=W0703
		from .. import fault
		try:
			fault.errors_add(exc, traceback.format_exc())
		except:
			pass
		raise

def print_except(func, *args, **kwargs):
	return print_except_helper(func, args, kwargs)

def start_thread(func, *args, **kwargs):
	return thread.start_new_thread(print_except_helper, (func, args, kwargs))

def parse_bool(x):
	"""
	Parses a boolean from a string. The values "True" "true" "False" "false" are recognized, all others result in an exception.
	@param x string
	"""
	if x == False or x == True:
		return x
	return {"true": True, "false": False}.get(str(x).lower())

class static:
	"""
	Allows to specify a method as static by using method=static(method)
	"""
	def __init__(self, anycallable):
		self.__call__ = anycallable

class curry:
	"""
	Allows to create new methods by currying.
	"""
	def __init__(self, fn, preargs=[], prekwargs={}, postargs=[], postkwargs={}):
		self.fn = fn
		self.preargs = preargs[:]
		self.prekwargs = prekwargs.copy()
		self.postargs = postargs[:]
		self.postkwargs = postkwargs.copy()

	def __call__(self, *curargs, **curkwargs):
		kwargs = {}
		kwargs.update(self.prekwargs)
		kwargs.update(curkwargs)
		kwargs.update(self.postkwargs)
		args = [] + self.preargs + list(curargs) + self.postargs
		f = self.fn
		return f(*args, **kwargs) #pylint: disable-msg=W0142

def get_attr(obj, name, default=None, res_type=None):
	"""
	Retrieves an attribute if it exists or the default value if not
	@param name the name of the attribute
	@param default the default value
	@param res_type the result type of the method
	"""
	if obj.hasAttribute(name):
		val = obj.getAttribute(name)
	else:
		val = default
	if res_type:
		return res_type(val)
	else:
		return val

def calculate_subnet4(ip_with_prefix):
	(ip, prefix) = ip_with_prefix.split("/")
	ip_num = 0
	for p in ip.split("."):
		ip_num = ip_num * 256 + int(p)
	mask = (1<<32) - (1<<(32-int(prefix)))
	ip_num = ip_num & mask
	ip = []
	while len(ip) < 4:
		ip.insert(0, str(ip_num % 256))
		ip_num = ip_num // 256
	return ".".join(ip)+"/"+prefix

def calculate_subnet6(ip_with_prefix):
	(ip, prefix) = ip_with_prefix.split("/")
	ip_num = 0
	ip = ip.split("::")
	ip1 = ip[0].split(":")
	if len(ip) > 1:
		ip2 = ip[1].split(":")
		while len(ip1)+len(ip2) < 8:
			ip1.append("0")
		for i in ip2:
			ip1.append(i)
	ip = ip1
	for p in ip:
		ip_num = (ip_num<<16) + int(p,16)
	mask = (1<<128) - (1<<(128-int(prefix)))
	ip_num = ip_num & mask
	ip = []
	while len(ip) < 8:
		ip.insert(0, hex(int(ip_num % (1<<16)))[2:])
		ip_num = ip_num // (1<<16)
	return ":".join(ip)+"/"+prefix

@xmlRpcSafe
def xml_rpc_sanitize(s):
	if s == None:
		return s
	if isinstance(s, str) or isinstance(s, float) or isinstance(s, unicode) or isinstance(s, bool):
		return s
	if isinstance(s, int) and abs(s) < (1<<31):
		return s
	if isinstance(s, int) and abs(s) >= (1<<31):
		return float(s)
	if isinstance(s, list):
		return [xml_rpc_sanitize(e) for e in s]
	if isinstance(s, dict):
		return dict([(str(k), xml_rpc_sanitize(v)) for k, v in s.iteritems()])
	return str(s)

def xml_rpc_safe(s):
	if s == None:
		return True
	if isinstance(s, str) or isinstance(s, float) or isinstance(s, unicode) or isinstance(s, bool):
		return True
	if isinstance(s, int) and abs(s) < (1<<31):
		return True
	if isinstance(s, list):
		for e in s:
			if not xml_rpc_safe(e):
				return False
		return True
	if isinstance(s, dict):
		for k, v in s.iteritems():
			if not xml_rpc_safe(k) or not xml_rpc_safe(v):
				return False
		return True
	print type(s)
	return False

def datestr(date):
	import datetime
	return datetime.datetime.fromtimestamp(date).strftime("%Y-%m-%d %H:%M:%S.%f")

def timediffstr(date1, date2):
	import datetime
	d1 = datetime.datetime.fromtimestamp(date1)
	d2 = datetime.datetime.fromtimestamp(date2)
	return str(d2-d1)

def waitFor(conditionFn, maxWait=5, waitStep=0.1):
	#wait up to 5 sec for interface to appear
	waited = 0
	while waited < maxWait and not conditionFn():
		time.sleep(waitStep)
		waited += waitStep
	return waited < maxWait

def filterDict(filter_, dict_):
	if not callable(filter_):
		filter_ = lambda (k, v): k in filter_
	return dict(filter(filter_, dict_.iteritems()))

def utcDatetimeToTimestamp(date):
	td = date - datetime.datetime(1970, 1, 1)
	return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

# Similar to update, but works recursively if a dict would overwrite a dict. e.g. join({a:{b:c}},{a:{d:e}}) == {a:{b:c,d:e}}
def joinDicts(dictA,dictB):
	if (type(dictA) is dict) and (type(dictB) is dict):
		A = dictA.copy()
		for i in dictB.keys():
			if (i in A) and (type(A[i]) is dict) and (type(dictB[i]) is dict):
				A[i] = join(A[i],dictB[i])
			else:
				A[i] = dictB[i]
	return A