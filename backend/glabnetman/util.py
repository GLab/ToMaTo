# -*- coding: utf-8 -*-

import subprocess, threading, thread

class RepeatedTimer(threading.Thread):
	def __init__(self, timeout, func, *args, **kwargs):
		self.timeout = timeout
		self.func = func
		self.args = args
		self.kwargs = kwargs
		threading.Thread.__init__(self)
		self.event = threading.Event()
		self.daemon = True
	def run(self):
		while not self.event.isSet():
			try:
				self.event.wait(self.timeout)
			except:
				return
			if not self.event.isSet():
				self.func(*self.args, **self.kwargs)
	def stop(self):
		self.event.set()

def print_except_helper(func, args, kwargs):
	try:
		return func(*args, **kwargs)
	except Exception, ex:
		print ex
		raise

def print_except(func, *args, **kwargs):
	return print_except_helper(func, args, kwargs)

def start_thread(func, *args, **kwargs):
	return thread.start_new_thread(print_except_helper, (func, args, kwargs))

def run_shell(cmd, pretend=False):
	if pretend:
		cmd.insert(0,"echo")
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	res=proc.communicate()
	return res[0]

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
	def __init__(self, fun, *args, **kwargs):
		self.fun = fun
		self.pending = args[:]
		self.kwargs = kwargs.copy()

	def __call__(self, selfref, *args, **kwargs):
		if kwargs and self.kwargs:
			kw = self.kwargs.copy()
			kw.update(kwargs)
		else:
			kw = kwargs or self.kwargs
		return self.fun(selfref, *(self.pending + args), **kw)

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

def calculate_subnet(ip_with_prefix):
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
