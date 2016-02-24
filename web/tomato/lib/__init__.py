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
import xmlrpclib, urllib, hashlib, time
import anyjson as json
import os
from .error import Error  # @UnresolvedImport
from .handleerror import renderError, ajaxError, renderFault, ajaxFault
from thread import start_new_thread
from versioninfo import getVersionStr
from .cmd import runUnchecked

from settings import get_settings, Config
from .. import settings as config_module
settings = get_settings(config_module)



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

class APIDurationLog:
	duration_log_config = settings.get_duration_log_settings()
	entry_count = duration_log_config['size']
	def __init__(self, enabled=True, filename=None):
		self.enabled = enabled
		self.filename = filename
		if enabled:
			if filename and os.path.exists(filename):
				try:
					with open(filename) as f:
						data = json.loads(f.read())
						self.durations = data['durations']
						self.counts = data['counts']
						self.total_durations = data['total_durations']
				except:
					self.durations = {}
					self.counts = {}
					self.total_durations = {}
			else:
				self.durations = {}
				self.counts = {}
				self.total_durations = {}

	def _save(self):
		if self.filename:
			with open(self.filename, 'w+') as f:
				f.write(json.dumps({
					'durations': self.durations,
					'counts': self.counts,
					'total_durations': self.total_durations
				}))

	def log_call(self, name, duration, args, kwargs):  # fixme: create args/kwargs depending logs
		if self.enabled:
			try:
				drs = self.durations[name]
				self.counts[name] += 1
				self.total_durations[name] += duration
			except KeyError:
				drs = []
				self.durations[name] = drs
				self.counts[name] = 1
				self.total_durations[name] = duration
			drs.append(duration)
			if len(drs) > APIDurationLog.entry_count:
				drs.pop(0)
			self._save()

	def get_api_durations(self):
		if self.enabled:
			return {k: {
				'duration': reduce(lambda x, y: x + y, self.durations[k]) / len(self.durations[k]),
				'count': self.counts[k],
				'total_duration': self.total_durations[k]
			} for k in self.durations.iterkeys()}
		return {}


def api_duration_log():
	duration_log_config = settings.get_duration_log_settings()
	return APIDurationLog(duration_log_config['enabled'], duration_log_config['location'])

def log_api_duration(name, duration, args, kwargs):
	api_duration_log().log_call(name, duration, args, kwargs)

class ServerProxy(object):
	def __init__(self, url, **kwargs):
		self._xmlrpc_server_proxy = xmlrpclib.ServerProxy(url, **kwargs)

	def __getattr__(self, name):
		call_proxy = getattr(self._xmlrpc_server_proxy, name)

		def _call(*args, **kwargs):
			import time
			try:
				before = time.time()
				res = call_proxy(args, kwargs)
				after = time.time()
				if settings.get_duration_log_settings()['enabled']:
					start_new_thread(
						log_api_duration,
						(),
						{'name': name, 'duration': after-before, 'args': args, 'kwargs': kwargs}
					)
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
	server_settings = settings.get_interface(Config.TOMATO_MODULE_BACKEND_API, False, 'http')  # fixme: use https, and ssl
	if server_settings is None:
		server_settings = settings.get_interface(Config.TOMATO_MODULE_BACKEND_API, False, 'http')
	try:
		if auth:
			api = ServerProxy('%s://%s:%s@%s:%s' % (
			server_settings['protocol'], username, password, server_settings['host'], server_settings['port']), allow_none=True)
			api.user = UserObj(api)
		else:
			api = ServerProxy('%s://%s:%s' % (server_settings['protocol'], server_settings['host'], server_settings['port']),
				allow_none=True)
			api.user = None
	except:
		import traceback
		traceback.print_exc()
		api = ServerProxy('%s://%s:%s' % (server_settings['protocol'], server_settings['host'], server_settings['port']),
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
			if 'user' in request.session:
				request.session['user'].checkUpdate(api)
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
				res = self.fun(api, request, *args, **data)
				return HttpResponse(json.dumps({"success": True, "result": res}))
			except Exception, e:
				return ajaxFault(e)
		except xmlrpclib.ProtocolError, e:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (e.errcode, e.errmsg)}),
				status=e.errcode if e.errcode in [401, 403] else 200)
		except xmlrpclib.Fault, f:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s' % f}))


@cached(600)
def serverInfo():
	return getapi().server_info()


import urllib2, re
from urlparse import urljoin


@cached(3600)
def getNews():
	url = settings.get_external_url(Config.EXTERNAL_URL_JSON_FEED)
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
	return getVersionStr()


def security_token(data, session=""):
	return hashlib.md5("%s|%s|%s" % (data, session, settings.get_secret_key())).hexdigest()


class UserObj:
	def __init__(self, api):
		self.updateData(api)

	def checkUpdate(self, api):
		if time.time() - self.data_time > settings.get_account_info_update_interval():
			self.updateData(api)

	def updateData(self, api):
		self.data = api.account_info()
		self.name = self.data["name"]
		self.flags = self.data["flags"]
		self.organization = self.data["organization"]
		self.realname = self.data["realname"]
		self.id = self.data["id"]
		self.notification_count = self.data['notification_count']
		self.data_time = time.time()

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
