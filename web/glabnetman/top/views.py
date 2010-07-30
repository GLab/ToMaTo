# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404

from lib import *

def index(request):
	if not getapi(request):
		return HttpResponseNotAuthorized("Authorization required!")
	api = request.session.api
	return render_to_response("top/index.html", {'top_list': api.top_list()})

def create(request):
	if not request.REQUEST.has_key("xml"):
		return render_to_response("top/create.html")
	xml=request.REQUEST["xml"]
	if not getapi(request):
		return HttpResponseNotAuthorized("Authorization required!")
	api = request.session.api
	top_id=api.top_import(xml)
	top=api.top_info(int(top_id))
	return render_to_response("top/detail.html", {'top_id': top_id, 'top': top})
	
def action(request, top_id, action=None):
	if not getapi(request):
		return HttpResponseNotAuthorized("Authorization required!")
	api = request.session.api
	if action=="showxml":
		xml=api.top_get(int(top_id))
		if request.REQUEST.has_key("plain"):
			return HttpResponse(xml, mimetype="text/plain")
		else:
			return render_to_response("top/showxml.html", {'top_id': top_id, 'xml': xml})
	if action=="remove":
		api.top_remove(int(top_id))
		return index(request)
	top=api.top_info(int(top_id))
	if not top:
		raise Http404
	output=None
	if action=="upload":
		output=api.top_upload(int(top_id))
	elif action=="prepare":
		output=api.top_prepare(int(top_id))
	elif action=="destroy":
		output=api.top_destroy(int(top_id))
	elif action=="start":
		output=api.top_start(int(top_id))
	elif action=="stop":
		output=api.top_stop(int(top_id))
	return render_to_response("top/detail.html", {'top_id': top_id, 'top': top, 'action' : action, 'output' : output })
