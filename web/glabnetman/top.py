# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404
from django.core.servers.basehttp import FileWrapper

from lib import *
import xmlrpclib, tempfile

def _display_top(api, top_id, task_id=None, action=None):
	top=api.top_info(int(top_id))
	return render_to_response("top/detail.html", {'top_id': top_id, 'top': top, 'action' : action, 'task_id' : task_id })

def index(api, request):
	host_filter = "*"
	if request.REQUEST.has_key("host_filter"):
		host_filter=request.REQUEST["host_filter"]
	owner_filter = "*"
	if request.REQUEST.has_key("owner_filter"):
		owner_filter=request.REQUEST["owner_filter"]
	toplist=api.top_list(owner_filter, host_filter, "user")
	return render_to_response("top/index.html", {'top_list': toplist})
index=wrap_rpc(index)

def create(api, request):
	if not request.REQUEST.has_key("xml"):
		tpl_openvz=",".join([t["name"] for t in api.template_list("openvz")])
		tpl_kvm=",".join([t["name"] for t in api.template_list("kvm")])
		host_groups=",".join(api.host_groups())
		if not request.REQUEST.has_key("editor"):
			editor = "ui"
		else:
			editor = request.REQUEST["editor"]
		return render_to_response("top/edit_%s.html" % editor, {'auth': request.META["HTTP_AUTHORIZATION"], 'tpl_openvz': tpl_openvz, 'tpl_kvm': tpl_kvm, 'host_groups': host_groups})
	xml=request.REQUEST["xml"]
	top_id=api.top_import(xml)
	return _display_top(api, top_id)
create=wrap_rpc(create)
	
def upload_image(api, request, top_id, device_id):
	if not request.FILES.has_key("image"):
		top=api.top_info(int(top_id))
		return render_to_response("top/upload.html", {'top_id': top_id, 'top': top, 'device_id': device_id} )
	file=request.FILES["image"]
	upload_id=api.upload_start()
	for chunk in file.chunks():
		api.upload_chunk(upload_id,xmlrpclib.Binary(chunk))
	task_id = api.upload_image(top_id, device_id, upload_id)
	return _display_top(api, top_id, task_id, "Upload image")
upload_image=wrap_rpc(upload_image)

def download_image(api, request, top_id, device_id):
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
	filename_ext = {'openvz': 'tgz', 'kvm': 'qcow2'}[dict(top['devices'])[device_id]['type']]
	response['Content-Disposition'] = 'attachment; filename=%s_%s.%s' % ( top["name"], device_id, filename_ext )
	return response
download_image=wrap_rpc(download_image)

def vncview(api, request, top_id, device_id):
	top=api.top_info(int(top_id))
	device=dict(top["devices"])[device_id]
	return render_to_response("top/vncview.html", {'top': top, 'device': device})
vncview=wrap_rpc(vncview)

def edit(api, request, top_id):
	if not request.REQUEST.has_key("xml"):
		xml=api.top_get(int(top_id))
		tpl_openvz=",".join([t["name"] for t in api.template_list("openvz")])
		tpl_kvm=",".join([t["name"] for t in api.template_list("kvm")])
		host_groups=",".join(api.host_groups())
		if not request.REQUEST.has_key("editor"):
			editor = "ui"
		else:
			editor = request.REQUEST["editor"]
		return render_to_response("top/edit_%s.html" % editor, {'top_id': top_id, 'xml': xml, 'auth': request.META["HTTP_AUTHORIZATION"], 'tpl_openvz': tpl_openvz, 'tpl_kvm': tpl_kvm, 'host_groups': host_groups} )
	xml=request.REQUEST["xml"]
	task_id=api.top_change(int(top_id), xml)
	return _display_top(api, top_id, task_id, "Change topology")
edit=wrap_rpc(edit)

def details(api, request, top_id):
	return _display_top(api, top_id)
details=wrap_rpc(details)
	
def showxml(api, request, top_id):
	xml=api.top_get(int(top_id), True)
	if request.REQUEST.has_key("plain"):
		return HttpResponse(xml, mimetype="text/plain")
	else:
		top=api.top_info(int(top_id))
		return render_to_response("top/showxml.html", {'top_id': top_id, 'top': top, 'xml': xml})
showxml=wrap_rpc(showxml)

def remove(api, request, top_id):
	api.top_remove(int(top_id))
	return index(request)
remove=wrap_rpc(remove)

def prepare(api, request, top_id):
	task_id=api.top_prepare(int(top_id))
	return _display_top(api, top_id, task_id, "Prepare topology")
prepare=wrap_rpc(prepare)

def destroy(api, request, top_id):
	task_id=api.top_destroy(int(top_id))
	return _display_top(api, top_id, task_id, "Destroy topology")
destroy=wrap_rpc(destroy)

def start(api, request, top_id):
	task_id=api.top_start(int(top_id))
	return _display_top(api, top_id, task_id, "Start topology")
start=wrap_rpc(start)

def stop(api, request, top_id):
	task_id=api.top_stop(int(top_id))
	return _display_top(api, top_id, task_id, "Stop topology")
stop=wrap_rpc(stop)

def dev_prepare(api, request, top_id, device_id):
	task_id=api.device_prepare(int(top_id), device_id)
	return _display_top(api, top_id, task_id, "Prepare device")
dev_prepare=wrap_rpc(dev_prepare)

def dev_destroy(api, request, top_id, device_id):
	task_id=api.device_destroy(int(top_id), device_id)
	return _display_top(api, top_id, task_id, "Destroy device")
dev_destroy=wrap_rpc(dev_destroy)

def dev_start(api, request, top_id, device_id):
	task_id=api.device_start(int(top_id), device_id)
	return _display_top(api, top_id, task_id, "Start device")
dev_start=wrap_rpc(dev_start)

def dev_stop(api, request, top_id, device_id):
	task_id=api.device_stop(int(top_id), device_id)
	return _display_top(api, top_id, task_id, "Stop device")
dev_stop=wrap_rpc(dev_stop)

def con_prepare(api, request, top_id, connector_id):
	task_id=api.connector_prepare(int(top_id), connector_id)
	return _display_top(api, top_id, task_id, "Prepare connector")
con_prepare=wrap_rpc(con_prepare)

def con_destroy(api, request, top_id, connector_id):
	task_id=api.connector_destroy(int(top_id), connector_id)
	return _display_top(api, top_id, task_id, "Destroy connector")
con_destroy=wrap_rpc(con_destroy)

def con_start(api, request, top_id, connector_id):
	task_id=api.connector_start(int(top_id), connector_id)
	return _display_top(api, top_id, task_id, "Start connector")
con_start=wrap_rpc(con_start)

def con_stop(api, request, top_id, connector_id):
	task_id=api.connector_stop(int(top_id), connector_id)
	return _display_top(api, top_id, task_id, "Stop connector")
con_stop=wrap_rpc(con_stop)

def permission_list(api, request, top_id):
	top=api.top_info(int(top_id))
	return render_to_response("top/permissions.html", {'top_id': top_id, 'top': top })
permission_list=wrap_rpc(permission_list)

def permission_remove(api, request, top_id, user):
	api.permission_remove(top_id, user)
	return permission_list(request, top_id)
permission_remove=wrap_rpc(permission_remove)

def permission_add(api, request, top_id):
	user=request.REQUEST["user"]
	role=request.REQUEST["role"]
	api.permission_add(top_id, user, role)
	return permission_list(request, top_id)
permission_add=wrap_rpc(permission_add)