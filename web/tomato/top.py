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
from django import forms

from lib import *
import xmlrpclib, tempfile
import simplejson as json
import zlib, base64

def _display_top(api, top_id, task_id=None, action=None):
	try:
		api.top_info(top_id)
	except:
		return HttpResponseRedirect(reverse('tomato.top.index')) 
	return render_to_response("top/edit_jsui.html", {'top_id': top_id, 'tpl_openvz': "", 'tpl_kvm': "", 'host_groups': "", "special_features": ""} )

@wrap_rpc
def index(api, request):
	host_filter = ""
	if request.REQUEST.has_key("host_filter"):
		host_filter=request.REQUEST["host_filter"]
	owner_filter = ""
	if request.REQUEST.has_key("owner_filter"):
		owner_filter=request.REQUEST["owner_filter"]
	toplist=api.top_list(owner_filter, host_filter)
	return render_to_response("top/index.html", {'top_list': toplist})

@wrap_rpc
def create(api, request):
	top_id=api.top_create()
	if request.REQUEST.has_key("json"):
		data = request.REQUEST["json"]
		try:
			top = json.loads(data)
		except:
			data = zlib.decompress(base64.b64decode(data))
			top = json.loads(data)
		mods = []
		mods.append({"type": "topology-rename", "element": None, "subelement": None, "properties": {"name": top["attrs"]["name"]}})
		for devname, dev in top["devices"].iteritems():
			mods.append({"type": "device-create", "element": None, "subelement": None, "properties": dev["attrs"]})
			for iface in dev["interfaces"].values():
				mods.append({"type": "interface-create", "element": devname, "subelement": None, "properties": iface["attrs"]})
		for conname, con in top["connectors"].iteritems():
			mods.append({"type": "connector-create", "element": None, "subelement": None, "properties": con["attrs"]})
			for c in con["connections"].values():
				c["attrs"]["interface"] = c["interface"]
				mods.append({"type": "connection-create", "element": conname, "subelement": None, "properties": c["attrs"]})
		api.top_modify(top_id, mods, True)
		return HttpResponseRedirect(reverse('tomato.top.show', kwargs={"top_id": top_id}))
	else:
		return HttpResponseRedirect(reverse('tomato.top.edit', kwargs={"top_id": top_id}))

def import_form(request):
	return render_to_response("top/import.html")

@wrap_rpc
def renew(api, request, top_id):
	api.top_action(int(top_id), "topology", None, "renew")
	return _display_top(api, top_id)

@wrap_rpc
def edit(api, request, top_id):
	try:
		api.top_info(top_id)
	except:
		return HttpResponseRedirect(reverse('tomato.top.index'))
	tpls = api.template_map()
	tpl_openvz=",".join([t["name"] for t in filter(lambda t: t.get("enabled", False), tpls.get("openvz", []))])
	tpl_kvm=",".join([t["name"] for t in filter(lambda t: t.get("enabled", False), tpls.get("kvm", []))])
	tpl_prog=",".join([t["name"] for t in filter(lambda t: t.get("enabled", False), tpls.get("prog", []))])
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
	return render_to_response("top/edit_%s.html" % editor, {'top_id': top_id, 'tpl_openvz': tpl_openvz, 'tpl_kvm': tpl_kvm, 'tpl_prog': tpl_prog, 'host_groups': host_groups, "external_networks": external_networks, 'edit':True} )

@wrap_rpc
def show(api, request, top_id):
	try:
		api.top_info(top_id)
	except:
		return HttpResponseRedirect(reverse('tomato.top.index')) 
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

class ExportForm(forms.Form):
	compress = forms.BooleanField(required=False)
	reduce = forms.BooleanField(required=False, initial=True)

@wrap_rpc
def export(api, request, top_id):
	def compressData(s):
		data = base64.b64encode(zlib.compress(s))
		return "\n".join([data[i:i+80] for i in range(0, len(data), 80)])
	blacklist=set(['capabilities', 'id', 'resources', 'vnc_port', 'vmid', 'host', 'vnc_password', 
 		'destroy_timeout', 'stop_timeout', 'remove_timeout', 'device_count', 'connector_count', 
  		'tinc_port', 'bridge_id', 'properties', 'used_network', 'finished_task', 'running_task'])
	def reduceData(data, blacklist):
		if isinstance(data, list):
			return [reduceData(el, blacklist) for el in data]
		if isinstance(data, dict):
			return dict(filter(lambda (k, v): k not in blacklist, [(k, reduceData(v, blacklist)) for k, v in data.iteritems()]))
		return data
	compress = False
	reduce = True
	if request.method == 'POST':
		form = ExportForm(request.POST)
		if form.is_valid():
			d = form.cleaned_data
			compress = d["compress"]
			reduce = d["reduce"]
	else:
		form = ExportForm()
	top=api.top_info(int(top_id))
	if reduce:
		top = reduceData(top, blacklist)
	top = json.dumps(top, indent=None if compress else "  ")
	if compress:
		top = compressData(top)
	if "download" in request.REQUEST:
		response = HttpResponse(top, content_type="text/plain")
		name = "topology_%s" % top_id
		if compress:
			name += ".gzip_b64.txt"
		else:
			name += ".json.txt"
		response['Content-Disposition'] = 'attachment; filename=' + name
		return response 
	return render_to_response("top/export.html", {"top_id": top_id, "top": top, "form": form}) 

def console(request):
	return render_to_response("top/console.html")