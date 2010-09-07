# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response

from lib import *
import xmlrpclib

def index(request):
	return render_to_response("main/base.html")

def error_list(request):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		errors = api.errors_all()
		print errors
		return render_to_response("admin/error_list.html", {'errors': errors})
	except xmlrpclib.Fault, f:
		print f
		return render_to_response("main/error.html", {'error': f})

def error_remove(request, error_id):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		api.errors_remove(error_id)
		return error_list(request)
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def task_list(request):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		tasks = api.task_list()
		return render_to_response("admin/task_list.html", {'tasks': tasks})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def task_status(request, task_id):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		task = api.task_status(task_id)
		backurl=""
		if request.REQUEST.has_key("backurl"):
			backurl=request.REQUEST["backurl"]
		return render_to_response("main/task.html", {'task': task, 'backurl': backurl})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def logout(request):
	return HttpResponseNotAuthorized("/")

def help(request, page=""):
	return HttpResponseRedirect("http://fileserver.german-lab.de/trac/glabnetman/wiki/%s" % page)