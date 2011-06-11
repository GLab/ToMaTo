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
import xmlrpclib, json
from settings import *

def getauth(request):
	if not request.META.has_key("HTTP_AUTHORIZATION"):
		return None
	authstr=request.META["HTTP_AUTHORIZATION"]
	(authmeth, auth) = authstr.split(' ',1)
	if 'basic' != authmeth.lower():
		return None
	auth = auth.strip().decode('base64')
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

def getapi(request):
	auth=getauth(request)
	if not auth:
		return None
	(username, password) = auth
	try:
		api = ServerProxy('%s://%s:%s@%s:%s' % (server_protocol, username, password, server_host, server_port), allow_none=True )
		api.account()
		return api
	except Exception, exc:
		import socket
		if isinstance(exc, socket.error):
			import os
			raise xmlrpclib.Fault(exc.errno, os.strerror(exc.errno))
		raise xmlrpclib.Fault("-1", "Unauthorized")
	return True

class HttpResponseNotAuthorized(HttpResponse):
	status_code = 401
	def __init__(self, redirect_to):
		HttpResponse.__init__(self)
		self['WWW-Authenticate'] = 'Basic realm="%s"' % server_httprealm

class wrap_rpc:
	def __init__(self, fun):
		self.fun = fun
	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			if api is None:
				return HttpResponseNotAuthorized("Authorization required!")
			return self.fun(api, request, *args, **kwargs) 
		except xmlrpclib.ProtocolError, e:
			f={"faultCode": e.errcode, "faultString": e.errmsg}
			return render_to_response("main/error.html", {'error': f})
		except xmlrpclib.Fault, f:
			return render_to_response("main/error.html", {'error': f})
		
class wrap_json:
	def __init__(self, fun):
		self.fun = fun
	def __call__(self, request, *args, **kwargs):
		try:
			api = getapi(request)
			if api is None:
				return HttpResponseNotAuthorized("Authorization required!")
			try:
				res = self.fun(api, request, *args, **kwargs)
				return HttpResponse(json.dumps({"success": True, "output": res}))
			except xmlrpclib.Fault, f:
				return HttpResponse(json.dumps({"success": False, "output": f.faultString}))
			except Exception, exc:
				return HttpResponse(json.dumps({"success": False, "output": '%s:%s' % (exc.__class__.__name__, exc)}))				
		except xmlrpclib.ProtocolError, e:
			return HttpResponse(json.dumps({"success": False, "output": 'Error %s: %s' % (e.errcode, e.errmsg)}))				
		except xmlrpclib.Fault, f:
			return HttpResponse(json.dumps({"success": False, "output": 'Error %s' % f}))