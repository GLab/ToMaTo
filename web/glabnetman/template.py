# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404

from lib import *
import xmlrpclib

def index(request):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		return render_to_response("admin/template_index.html", {'templates': api.template_list("*")})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def add(request):
	try:
		if not request.REQUEST.has_key("name"):
			return render_to_response("admin/template_add.html")
		name=request.REQUEST["name"]
		type=request.REQUEST["type"]
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		api.template_add(name, type)
		return index(request)
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def remove(request, name):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		api.template_remove(name)
		return index(request)
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def set_default(request, type, name):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		api.template_set_default(type, name)
		return index(request)
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})
