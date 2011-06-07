# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import Http404
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib, tempfile

def _display_top(api, top_id, task_id=None, action=None):
	#FIXME: check for existence
	return render_to_response("top/edit_jsui.html", {'top_id': top_id, 'tpl_openvz': "", 'tpl_kvm': "", 'host_groups': "", "special_features": ""} )

@wrap_rpc
def index(api, request):
	host_filter = ""
	if request.REQUEST.has_key("host_filter"):
		host_filter=request.REQUEST["host_filter"]
	owner_filter = ""
	if request.REQUEST.has_key("owner_filter"):
		owner_filter=request.REQUEST["owner_filter"]
	toplist=api.top_list(owner_filter, host_filter, "user")
	return render_to_response("top/index.html", {'top_list': toplist})

@wrap_rpc
def create(api, request):
	top_id=api.top_create()
	if request.REQUEST.has_key("json"):
		import simplejson as json
		top = json.loads(request.REQUEST["json"])
		mods = []
		mods.append({"type": "topology-rename", "element": None, "subelement": None, "properties": {"name": top["attrs"]["name"]}})
		for devname, dev in top["devices"].iteritems():
			mods.append({"type": "device-create", "element": None, "subelement": None, "properties": dev["attrs"]})
			for iface in dev["interfaces"].values():
				mods.append({"type": "interface-create", "element": devname, "subelement": None, "properties": iface["attrs"]})
		for conname, con in top["connectors"].iteritems():
			mods.append({"type": "connector-create", "element": None, "subelement": None, "properties": con["attrs"]})
			for c in con["connections"].values():
				mods.append({"type": "connection-create", "element": conname, "subelement": None, "properties": c["attrs"]})
		api.top_modify(top_id, mods, True)
		return HttpResponseRedirect(reverse('tomato.top.show', kwargs={"top_id": top_id}))
	else:
		return HttpResponseRedirect(reverse('tomato.top.edit', kwargs={"top_id": top_id}))

def import_form(request):
	return render_to_response("top/import.html")

@wrap_rpc
def download_capture(api, request, top_id, connector_id, device_id, interface_id):
	top=api.top_info(int(top_id))
	download_id=api.download_capture(top_id, connector_id, device_id, interface_id)
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
	response['Content-Disposition'] = 'attachment; filename=capture_%s_%s_%s_%s.tar.gz' % ( top["name"], connector_id, device_id, interface_id )
	return response

@wrap_rpc
def renew(api, request, top_id):
	api.top_action(int(top_id), "topology", None, "renew")
	return _display_top(api, top_id)

@wrap_rpc
def edit(api, request, top_id):
	#FIXME: check for existence
	tpl_openvz=",".join([t["name"] for t in api.template_list("openvz")])
	tpl_kvm=",".join([t["name"] for t in api.template_list("kvm")])
	enlist = api.external_networks()
	map = {}
	for en in enlist:
		if map.has_key(en["type"]):
			map[en["type"]].append(en["group"])
		else:
			map[en["type"]] = [en["group"]]
	external_networks=",".join([f+":"+("|".join(map[f])) for f in map])
	host_groups=",".join(api.host_groups())
	if not request.REQUEST.has_key("editor"):
		editor = "jsui"
	else:
		editor = request.REQUEST["editor"]
	return render_to_response("top/edit_%s.html" % editor, {'top_id': top_id, 'tpl_openvz': tpl_openvz, 'tpl_kvm': tpl_kvm, 'host_groups': host_groups, "external_networks": external_networks, 'edit':True} )

@wrap_rpc
def show(api, request, top_id):
	if not request.REQUEST.has_key("format"):
		format = "jsui"
	else:
		format = request.REQUEST["format"]
	if format == "json":
		import json
		return HttpResponse(json.dumps(api.top_info(top_id), indent=2), mimetype="text/plain")		
	return render_to_response("top/edit_%s.html" % format, {'top_id': top_id, 'tpl_openvz': "", 'tpl_kvm': "", 'host_groups': "", "special_features": ""} )

@wrap_rpc
def remove(api, request, top_id):
	api.top_action(int(top_id), "remove", "topology", None)
	return index(request)

@wrap_rpc
def prepare(api, request, top_id):
	task_id=api.top_action(int(top_id), "prepare", "topology", None)
	return _display_top(api, top_id, task_id, "Prepare topology")

@wrap_rpc
def destroy(api, request, top_id):
	task_id=api.top_action(int(top_id), "destroy", "topology", None)
	return _display_top(api, top_id, task_id, "Destroy topology")

@wrap_rpc
def start(api, request, top_id):
	task_id=api.top_action(int(top_id), "start", "topology", None)
	return _display_top(api, top_id, task_id, "Start topology")

@wrap_rpc
def stop(api, request, top_id):
	task_id=api.top_action(int(top_id), "stop", "topology", None, "stop")
	return _display_top(api, top_id, task_id, "Stop topology")

@wrap_rpc
def dev_prepare(api, request, top_id, device_id):
	task_id=api.top_action(int(top_id), "prepare", "device", device_id)
	return _display_top(api, top_id, task_id, "Prepare device")

@wrap_rpc
def dev_destroy(api, request, top_id, device_id):
	task_id=api.top_action(int(top_id), "destroy", "device", device_id)
	return _display_top(api, top_id, task_id, "Destroy device")

@wrap_rpc
def dev_start(api, request, top_id, device_id):
	task_id=api.top_action(int(top_id), "start", "device", device_id)
	return _display_top(api, top_id, task_id, "Start device")

@wrap_rpc
def dev_stop(api, request, top_id, device_id):
	task_id=api.top_action(int(top_id), "stop", "device", device_id)
	return _display_top(api, top_id, task_id, "Stop device")

@wrap_rpc
def con_prepare(api, request, top_id, connector_id):
	task_id=api.top_action(int(top_id), "prepare", "connector", connector_id)
	return _display_top(api, top_id, task_id, "Prepare connector")

@wrap_rpc
def con_destroy(api, request, top_id, connector_id):
	task_id=api.top_action(int(top_id), "destroy", "connector", connector_id)
	return _display_top(api, top_id, task_id, "Destroy connector")

@wrap_rpc
def con_start(api, request, top_id, connector_id):
	task_id=api.top_action(int(top_id), "start", "connector", connector_id)
	return _display_top(api, top_id, task_id, "Start connector")

@wrap_rpc
def con_stop(api, request, top_id, connector_id):
	task_id=api.top_action(int(top_id), "stop", "connector", connector_id)
	return _display_top(api, top_id, task_id, "Stop connector")

@wrap_rpc
def permission_list(api, request, top_id):
	top=api.top_info(int(top_id))
	return render_to_response("top/permissions.html", {'top_id': top_id, 'top': top })

@wrap_rpc
def permission_set(api, request, top_id):
	user=request.REQUEST["user"]
	role=request.REQUEST["role"]
	api.permission_set(top_id, user, role)
	return permission_list(request, top_id)

def console(request):
	return render_to_response("top/console.html")