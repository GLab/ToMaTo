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
	request.session.api = xmlrpclib.ServerProxy('http://%s:%s@localhost:8000' % (username, password) )
	return True

class HttpResponseNotAuthorized(HttpResponse):
	status_code = 401
	def __init__(self, redirect_to):
		HttpResponse.__init__(self)
		self['WWW-Authenticate'] = 'Basic realm="%s"' % httprealm

