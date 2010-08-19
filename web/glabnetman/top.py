# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404
from django.core.servers.basehttp import FileWrapper

from lib import *
import xmlrpclib, tempfile

def index(request):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		host_filter = "*"
		if request.REQUEST.has_key("host_filter"):
			host_filter=request.REQUEST["host_filter"]
		owner_filter = "*"
		if request.REQUEST.has_key("owner_filter"):
			owner_filter=request.REQUEST["owner_filter"]
		state_filter = "*"
		if request.REQUEST.has_key("state_filter"):
			state_filter=request.REQUEST["state_filter"]
		toplist=api.top_list(state_filter, owner_filter, host_filter)
		return render_to_response("top/index.html", {'top_list': toplist})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def create(request):
	try:
		if not request.REQUEST.has_key("xml"):
			return render_to_response("top/create.html")
		xml=request.REQUEST["xml"]
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		top_id=api.top_import(xml)
		top=api.top_info(int(top_id))
		return render_to_response("top/detail.html", {'top_id': top_id, 'top': top})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})
	
def upload_image(request, top_id, device_id):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		if not request.FILES.has_key("image"):
			top=api.top_info(int(top_id))
			return render_to_response("top/upload.html", {'top_id': top_id, 'top': top, 'device_id': device_id} )
		file=request.FILES["image"]
		upload_id=api.upload_start()
		for chunk in file.chunks():
			api.upload_chunk(upload_id,xmlrpclib.Binary(chunk))
		task_id = api.upload_image(top_id, device_id, upload_id)
		top=api.top_info(int(top_id))
		return render_to_response("top/detail.html", {'top_id': top_id, 'top': top, 'action': 'upload', 'task_id': task_id})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})
	

def download_image(request, top_id, device_id):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		top=api.top_info(int(top_id))
		download_id=api.download_image(top_id, device_id)
		temp = tempfile.TemporaryFile()
		while True:
			data = api.download_chunk(download_id).data
			if len(data) == 0:
				break
			temp.write(data)
		size = temp.tell()
		temp.seek(0)
		wrapper = FileWrapper(temp)
		response = HttpResponse(wrapper, content_type='application/force-download')
		response['Content-Length'] = size
		response['Content-Disposition'] = 'attachment; filename=%s_%s.tgz' % ( top["name"], device_id )
		return response
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def vncview(request, top_id, device_id):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		top=api.top_info(int(top_id))
		device=dict(top["devices"])[device_id]
		return render_to_response("top/vncview.html", {'top': top, 'device': device})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def edit(request, top_id):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		if not request.REQUEST.has_key("xml"):
			xml=api.top_get(int(top_id))
			return render_to_response("top/edit.html", {'top_id': top_id, 'xml': xml} )
		xml=request.REQUEST["xml"]
		task_id=api.top_change(int(top_id), xml)
		top=api.top_info(int(top_id))
		return render_to_response("top/detail.html", {'top_id': top_id, 'top': top, 'action': 'change', 'task_id': task_id})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def details(request, top_id):
	return _action(request, top_id, "")
	
def showxml(request, top_id):
	return _action(request, top_id, "showxml")

def remove(request, top_id):
	return _action(request, top_id, "remove")

def prepare(request, top_id):
	return _action(request, top_id, "prepare")

def destroy(request, top_id):
	return _action(request, top_id, "destroy")

def start(request, top_id):
	return _action(request, top_id, "start")

def stop(request, top_id):
	return _action(request, top_id, "stop")

def _action(request, top_id, action):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		if action=="showxml":
			xml=api.top_get(int(top_id))
			if request.REQUEST.has_key("plain"):
				return HttpResponse(xml, mimetype="text/plain")
			else:
				top=api.top_info(int(top_id))
				return render_to_response("top/showxml.html", {'top_id': top_id, 'top': top, 'xml': xml})
		if action=="remove":
			api.top_remove(int(top_id))
			return index(request)
		task_id=None
		if action=="upload":
			task_id=api.top_upload(int(top_id))
		elif action=="prepare":
			task_id=api.top_prepare(int(top_id))
		elif action=="destroy":
			task_id=api.top_destroy(int(top_id))
		elif action=="start":
			task_id=api.top_start(int(top_id))
		elif action=="stop":
			task_id=api.top_stop(int(top_id))
		top=api.top_info(int(top_id))
		if not top:
			raise Http404
		return render_to_response("top/detail.html", {'top_id': top_id, 'top': top, 'action' : action, 'task_id' : task_id })
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})
