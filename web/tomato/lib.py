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
import xmlrpclib
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

def getapi(request):
	auth=getauth(request)
	if not auth:
		return None
	(username, password) = auth
	try:
		api = xmlrpclib.ServerProxy('%s://%s:%s@%s:%s' % (server_protocol, username, password, server_host, server_port) )
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