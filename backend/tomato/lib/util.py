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

import subprocess, threading, thread, traceback, time
from decorators import *
import exceptions

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
			except: #pylint: disable-msg=W0702
				return
			if not self.event.isSet():
				try:
					self.func(*self.args, **self.kwargs)
				except Exception, exc: #pylint: disable-msg=W0703
					from tomato import fault
					fault.log(exc)
	def stop(self):
		self.event.set()

def print_except_helper(func, args, kwargs):
	try:
		return func(*args, **kwargs) #pylint: disable-msg=W0142
	except Exception, exc: #pylint: disable-msg=W0703
		from tomato import fault
		try:
			traceback.print_exc()
			fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
		except:
			pass
		raise

def print_except(func, *args, **kwargs):
	return print_except_helper(func, args, kwargs)

def start_thread(func, *args, **kwargs):
	return thread.start_new_thread(print_except_helper, (func, args, kwargs))

def lines(str):
	return str.strip().split("\n")

def run_shell(cmd, shell=False):
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell, close_fds=True)
	res=proc.communicate()
	return (proc.returncode,)+res

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

def nothing():
	pass

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

def removeControlChars(s):
	#allow TAB=9, LF=10, CR=13
	controlChars = "".join(map(chr, range(0,9)+range(11,13)+range(14,32)))
	return s.translate(None, controlChars)

def escape(s):
	return repr(unicode(s).encode("utf-8"))

def sendMail(to, subject, body):
	import smtplib
	from email.mime.text import MIMEText
	from tomato import config
	if not config.MAIL.get("ENABLED", True):
		print "Mail sending is disabled"
		return
	msg = MIMEText(body)
	msg["Subject"] = subject
	msg["From"] = "%s <%s>" % (config.MAIL["SENDER_NAME"], config.MAIL["SENDER_MAIL"])
	msg["To"] = to
	s = smtplib.SMTP(config.MAIL["SERVER"])
	s.sendmail(config.MAIL["SENDER_MAIL"], [to], msg.as_string())
	s.quit()
	
def identifier(s, allowed="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_.", subst="_"):
	ret=""
	for ch in s:
		if ch in allowed:
			ret += ch
		elif subst:
			ret += subst
	return ret
	
class Localhost:
	def execute(self, cmd):
		res = run_shell(cmd, shell=True)
		if res[0] != 0:
			raise exceptions.CommandError("localhost", cmd, res[0], res[1])
		return res[1]
localhost = Localhost()
	