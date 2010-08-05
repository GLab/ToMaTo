# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response

from lib import *
import xmlrpclib

def index(request):
	return render_to_response("main/base.html")

def task_status(request, task_id):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		task = api.task_status(task_id)
		return render_to_response("main/task.html", {'task': task})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def logout(request):
	return HttpResponseNotAuthorized("/")