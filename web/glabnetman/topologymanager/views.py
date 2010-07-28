# -*- coding: utf-8 -*-

import xmlrpclib
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404

api=xmlrpclib.ServerProxy('http://admin:test@localhost:8000')

def index(request):
	return render_to_response("topologymanager/index.html", {'top_list': api.top_list()})
    
def detail(request, top_id):
	top=api.top_info(int(top_id))
	if not top:
		raise Http404
	else:
		return render_to_response("topologymanager/detail.html", {'top': top})
		
def showxml(request, top_id):
	xml=api.top_get(int(top_id))
	if not xml:
		raise Http404
	else:
		if request.REQUEST.has_key("plain"):
			return HttpResponse(xml, mimetype="text/plain")
		else:
			return render_to_response("topologymanager/showxml.html", {'xml': xml, 'top_id': top_id})
		
def remove(request, top_id):
	api.top_remove(int(top_id))
	return index(request)

def deploy(request, top_id):
	api.top_deploy(int(top_id))
	return detail(request, top_id)
	
def create(request, top_id):
	api.top_create(int(top_id))
	return detail(request, top_id)
	
def destroy(request, top_id):
	api.top_destroy(int(top_id))
	return detail(request, top_id)
	
def start(request, top_id):
	api.top_start(int(top_id))
	return detail(request, top_id)
	
def stop(request, top_id):
	api.top_stop(int(top_id))
	return detail(request, top_id)