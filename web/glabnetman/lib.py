# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
import xmlrpclib

httprealm="Glab Network Manager"

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
		api = xmlrpclib.ServerProxy('http://%s:%s@localhost:8000' % (username, password) )
		api.account()
		return api
	except:
		raise xmlrpclib.Fault("-1", "Unauthorized")
	return True

class HttpResponseNotAuthorized(HttpResponse):
	status_code = 401
	def __init__(self, redirect_to):
		HttpResponse.__init__(self)
		self['WWW-Authenticate'] = 'Basic realm="%s"' % httprealm

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