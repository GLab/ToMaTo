# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response

httprealm="Glab Network Manager"

class HttpResponseNotAuthorized(HttpResponse):
	status_code = 401
	def __init__(self, redirect_to):
		HttpResponse.__init__(self)
		self['WWW-Authenticate'] = 'Basic realm="%s"' % httprealm

def index(request):
	return render_to_response("main/base.html")

def logout(request):
	return HttpResponseNotAuthorized("/")