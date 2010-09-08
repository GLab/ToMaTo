# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response

from lib import *
import xmlrpclib

def index(request):
	return render_to_response("main/base.html")

def error_list(api, request):
	errors = api.errors_all()
	return render_to_response("admin/error_list.html", {'errors': errors})
error_list=wrap_rpc(error_list)

def error_remove(api, request, error_id):
	api.errors_remove(error_id)
	return error_list(api, request)
error_remove=wrap_rpc(error_remove)

def task_list(api, request):
	tasks = api.task_list()
	return render_to_response("admin/task_list.html", {'tasks': tasks})
task_list=wrap_rpc(task_list)

def task_status(api, request, task_id):
	task = api.task_status(task_id)
	backurl=""
	if request.REQUEST.has_key("backurl"):
		backurl=request.REQUEST["backurl"]
	return render_to_response("main/task.html", {'task': task, 'backurl': backurl})
task_status=wrap_rpc(task_status)

def help(request, page=""):
	return HttpResponseRedirect("http://fileserver.german-lab.de/trac/glabnetman/wiki/%s" % page)