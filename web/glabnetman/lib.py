# -*- coding: utf-8 -*-

from django.http import HttpResponse
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
		request.session.api = api
		api.account()
	except:
		raise xmlrpclib.Fault("-1", "Unauthorized")
	return True

class HttpResponseNotAuthorized(HttpResponse):
	status_code = 401
	def __init__(self, redirect_to):
		HttpResponse.__init__(self)
		self['WWW-Authenticate'] = 'Basic realm="%s"' % httprealm

