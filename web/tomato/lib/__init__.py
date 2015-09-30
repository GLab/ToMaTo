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

from django.http import HttpResponse
import xmlrpclib, urllib, hashlib
from . import anyjson as json
from .. import settings
from .error import Error  # @UnresolvedImport
from .handleerror import renderError, ajaxError, renderFault, ajaxFault


def getauth(request):
	auth = request.session.get("auth")
	if not auth:
		return None
	username, password = auth.split(':', 1)
	return (username, password)


class CachedMethod:
	def __init__(self, timeout, fn):
		self.timeout = timeout
		self.fn = fn
		self.time = None
		self.cache = None
		self.__name__ = fn.__name__
		self.__doc__ = fn.__doc__

	def __call__(self, *args, **kwargs):
		import time
		if self.time and self.time + self.timeout > time.time():
			return self.cache
		self.cache = self.fn(*args, **kwargs)
		self.time = time.time()
		return self.cache


def cached(timeout):
	def wrap(fn):
		_cache = None
		_time = None
		return CachedMethod(timeout, fn)

	return wrap


class AuthError(Exception):
	pass


class ServerProxy(object):
	def __init__(self, url, **kwargs):
		self._xmlrpc_server_proxy = xmlrpclib.ServerProxy(url, **kwargs)

	def __getattr__(self, name):
		call_proxy = getattr(self._xmlrpc_server_proxy, name)

		def _call(*args, **kwargs):
			import time
			before = time.time()
			try:
				# print "%s(%s, %s)" % (name, args, kwargs)
				res = call_proxy(args, kwargs)
				after = time.time()
				# print "%f, %s(%s, %s) -> %s" % (after-before, name, args, kwargs, res)
				print "%f, %s(%s, %s)" % (after - before, name, args, kwargs)
				return res
			except xmlrpclib.Fault, e:
				if e.faultCode == 999:
					e = Error.parsestr(e.faultString)
					raise e
				raise

		return _call


def getapi(request=None):
	auth = None
	if request:
		auth = getauth(request)
	if auth:
		(username, password) = auth
		username = urllib.quote_plus(username)
		password = urllib.quote_plus(password)
	try:
		if auth:
			api = ServerProxy('%s://%s:%s@%s:%s' % (
			settings.server_protocol, username, password, settings.server_host, settings.server_port), allow_none=True)
			api.user = UserObj(api)
		else:
			api = ServerProxy('%s://%s:%s' % (settings.server_protocol, settings.server_host, settings.server_port),
				allow_none=True)
			api.user = None
	except:
		import traceback
		traceback.print_exc()
		api = ServerProxy('%s://%s:%s' % (settings.server_protocol, settings.server_host, settings.server_port),
			allow_none=True)
		api.user = None
	if request:
		request.session.user = api.user
	return api


class wrap_rpc:
	def __init__(self, fun):
		self.fun = fun
		self.__name__ = fun.__name__
		self.__module__ = fun.__module__

	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			return self.fun(api, request, *args, **kwargs)
		except Exception, e:
			return renderFault(request, e)


class wrap_json:
	def __init__(self, fun):
		self.fun = fun

	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			data = json.loads(request.REQUEST["data"]) if request.REQUEST.has_key("data") else {}
			data.update(kwargs)
			try:
				res = self.fun(api, *args, **data)
				return HttpResponse(json.dumps({"success": True, "result": res}))
			except Exception, e:
				return ajaxFault(e)
		except xmlrpclib.ProtocolError, e:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (e.errcode, e.errmsg)}),
				status=e.errcode if e.errcode in [401, 403] else 200)
		except xmlrpclib.Fault, f:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s' % f}))


DEVNULL = open("/dev/null", "w")


def runUnchecked(cmd, shell=False, ignoreErr=False, input=None, cwd=None):  # @ReservedAssignment
	import subprocess
	stderr = DEVNULL if ignoreErr else subprocess.STDOUT
	stdin = subprocess.PIPE if input else None
	proc = subprocess.Popen(cmd, cwd=cwd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr, shell=shell,
		close_fds=True)
	res = proc.communicate(input)
	return (proc.returncode, res[0])


def getDpkgVersionStr(package):
	fields = {}
	error, output = runUnchecked(["dpkg-query", "-s", package])
	if error:
		return None
	for line in output.splitlines():
		if ": " in line:
			name, value = line.split(": ")
			fields[name.lower()] = value
	if not "installed" in fields["status"]:
		return None
	return fields["version"]


@cached(600)
def serverInfo():
	return getapi().server_info()


import urllib2, re
from urlparse import urljoin


@cached(3600)
def getNews():
	infs = serverInfo()["external_urls"]
	if "json_feed" in infs:
		url = serverInfo()["external_urls"]["json_feed"]
	else:
		url = serverInfo()["external_urls"]["news_feed"]

	news = json.load(urllib2.urlopen(url))
	pattern = re.compile("<[^>]+((?:src|href)=(?:[\"']([^\"']+)[\"']))[^>]*>")
	for item in news["items"]:
		desc = item["description"]
		for term, url in pattern.findall(desc):
			if url.startswith("mailto:") or url.startswith("&#109;&#097;&#105;&#108;&#116;&#111;:"):
				continue
			nurl = urljoin(item["link"], url)
			nterm = term.replace(url, nurl)
			desc = desc.replace(term, nterm)
		item["description"] = desc
	news["items"] = news["items"][:3]
	return news


@cached(3600)
def getVersion():
	return getDpkgVersionStr("tomato-web") or "devel"


def security_token(data, session=""):
	return hashlib.md5("%s|%s|%s" % (data, session, settings.SECRET_KEY)).hexdigest()


class UserObj:
	def __init__(self, api):
		self.data = api.account_info()
		self.name = self.data["name"]
		self.flags = self.data["flags"]
		self.origin = self.data["origin"]
		self.organization = self.data["organization"]
		self.realname = self.data["realname"]
		self.id = self.data["id"]

	def hasGlobalToplFlags(self):
		for flag in ["global_topl_owner", "global_topl_manager", "global_topl_user"]:
			if flag in self.flags:
				return True
		return False

	def hasOrgaToplFlags(self, orgaName=None):
		for flag in ["orga_topl_owner", "orga_topl_manager", "orga_topl_user"]:
			if flag in self.flags and (self.organization == orgaName or orgaName is None):
				return True
		return False

	def isAdmin(self, orgaName=None):
		if "global_admin" in self.flags:
			return True
		if "orga_admin" in self.flags and (self.organization == orgaName or orgaName is None):
			return True
		return False

	def isGlobalAdmin(self):
		return "global_admin" in self.flags

	def isHostManager(self, orgaName=None):
		if "global_host_manager" in self.flags:
			return True
		print self.flags
		if "orga_host_manager" in self.flags and (self.organization == orgaName or orgaName is None):
			return True
		return False

	def isGlobalHostManager(self):
		return "global_host_manager" in self.flags

	def hasDebugFlag(self):
		return "debug" in self.flags
