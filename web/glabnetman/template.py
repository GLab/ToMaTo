# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404

from lib import *
import xmlrpclib

def index(api, request):
	return render_to_response("admin/template_index.html", {'templates': api.template_list("*")})
index=wrap_rpc(index)

def add(api, request):
	name=request.REQUEST["name"]
	type=request.REQUEST["type"]
	api.template_add(name, type)
	return index(request)
add=wrap_rpc(add)

def remove(api, request, name):
	api.template_remove(name)
	return index(request)
remove=wrap_rpc(remove)

def set_default(api, request, type, name):
	api.template_set_default(type, name)
	return index(request)
set_default=wrap_rpc(set_default)