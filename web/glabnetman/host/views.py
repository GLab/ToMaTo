# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404

from lib import *

def index(request):
	if not getapi(request):
		return HttpResponseNotAuthorized("Authorization required!")
	api = request.session.api
	return render_to_response("host/index.html", {'host_list': api.host_list()})

def add(request):
	if not request.REQUEST.has_key("hostname"):
		return render_to_response("host/add.html")
	hostname=request.REQUEST["hostname"]
	if not getapi(request):
		return HttpResponseNotAuthorized("Authorization required!")
	api = request.session.api
	api.host_add(hostname)
	return render_to_response("host/index.html", {'host_list': api.host_list()})

def remove(request):
	hostname=request.REQUEST["hostname"]
	if not getapi(request):
		return HttpResponseNotAuthorized("Authorization required!")
	api = request.session.api
	api.host_remove(hostname)
	return render_to_response("host/index.html", {'host_list': api.host_list()})
