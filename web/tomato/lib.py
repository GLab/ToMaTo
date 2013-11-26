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
from django.shortcuts import render_to_response
import xmlrpclib, json, urllib, socket
from settings import *
import tags

def getauth(request):
	auth = request.session.get("auth")
	if request.META.has_key("HTTP_AUTHORIZATION"):
		authstr=request.META["HTTP_AUTHORIZATION"]
		(authmeth, auth) = authstr.split(' ',1)
		if 'basic' != authmeth.lower():
			return None
		auth = auth.strip().decode('base64')
		request.session["auth"] = auth
	if not auth:
		return None
	username, password = auth.split(':',1)
	return (username, password)

class ServerProxy(object):
	def __init__(self, url, **kwargs):
		self._xmlrpc_server_proxy = xmlrpclib.ServerProxy(url, **kwargs)
	def __getattr__(self, name):
		call_proxy = getattr(self._xmlrpc_server_proxy, name)
		def _call(*args, **kwargs):
			return call_proxy(args, kwargs)
		return _call

def getGuestApi():
	api = ServerProxy('%s://%s:%s@%s:%s' % (server_protocol, guest_username, guest_password, server_host, server_port), allow_none=True )
	api.user = UserObj(api)
	return api

def getapi(request):
	auth=getauth(request)
	if not auth:
		return None
	(username, password) = auth
	username = urllib.quote_plus(username)
	password = urllib.quote_plus(password)
	api = ServerProxy('%s://%s:%s@%s:%s' % (server_protocol, username, password, server_host, server_port), allow_none=True )
	api.user = UserObj(api)
	return api

class HttpResponseNotAuthorized(HttpResponse):
	status_code = 401
	def __init__(self, code=401, text=""):
		HttpResponse.__init__(self)
		self.status_code = code
		self['WWW-Authenticate'] = 'Basic realm="%s"' % server_httprealm
		self.write(text)

class wrap_rpc:
	def __init__(self, fun):
		self.fun = fun
	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			if api is None:
				return HttpResponseNotAuthorized()
			return self.fun(api, request, *args, **kwargs)
		except Exception, e:
			import traceback
			traceback.print_exc()
			if isinstance(e, socket.error):
				import os
				etype = "Socket error"
				ecode = e.errno
				etext = os.strerror(e.errno)
			elif isinstance(e, xmlrpclib.ProtocolError):
				etype = "RPC protocol error"
				ecode = e.errcode
				etext = e.errmsg
				if ecode == 401:
					return HttpResponseNotAuthorized()
			elif isinstance(e, xmlrpclib.Fault):
				etype = "RPC call error"
				ecode = e.faultCode
				etext = e.faultString
			else:
				etype = e.__class__.__name__
				ecode = ""
				etext = e.message
			return render_to_response("main/error.html", {'type': etype, 'code': ecode, 'text': etext})
		
class wrap_json:
	def __init__(self, fun):
		self.fun = fun
	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			if api is None:
				return HttpResponseNotAuthorized()
			data = json.loads(request.REQUEST["data"]) if request.REQUEST.has_key("data") else {}
			data.update(kwargs)
			try:
				res = self.fun(api, *args, **data)
				return HttpResponse(json.dumps({"success": True, "result": res}))
			except xmlrpclib.Fault, f:
				return HttpResponse(json.dumps({"success": False, "error": f.faultString}))
			except Exception, exc:
				return HttpResponse(json.dumps({"success": False, "error": '%s:%s' % (exc.__class__.__name__, exc)}))				
		except xmlrpclib.ProtocolError, e:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (e.errcode, e.errmsg)}))				
		except xmlrpclib.Fault, f:
			return HttpResponse(json.dumps({"success": False, "error": 'Error %s' % f}))

class UserObj:
	def __init__(self, api):
		self._api = api
		self.data = api.account_info()
		self.name = self.data["name"]
		self.flags = self.data["flags"]
		self.origin = self.data["origin"]
		self.organization = self.data["organization"]
	def isAdmin(self, orgaName=None):
		if "global_admin" in self.flags:
			return True
		if "orga_admin" in self.flags and self.organization == orgaName:
			return True
		return False
	def isHostManager(self, orgaName=None):
		if "global_host_manager" in self.flags:
			return True
		if "orga_host_manager" in self.flags and self.organization == orgaName:
			return True
		return False
	def isHostManagerForSite(self, site):
		orga = self._api.site_info(site)["organization"]
		return self.isHostManager(orga)