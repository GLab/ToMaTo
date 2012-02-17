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

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404
from django.core.servers.basehttp import FileWrapper
import simplejson as json
from django.core.urlresolvers import reverse

from lib import *

@wrap_json
def template_info(api, request, type, name):
	tpl = api.template_info(type, name)
	return tpl

@wrap_json
def modify(api, request, top_id):
	if not request.REQUEST.has_key("mods"):
		raise Exception("mods not found") 
	mods = json.loads(request.REQUEST["mods"])
	res = api.top_modify(top_id, mods, True)
	if res["status"] == "failed":
		raise Exception(res);
	return res

@wrap_json
def info(api, request, top_id):
	res = api.top_info(top_id);
	return res

@wrap_json
def action(api, request, top_id):
	if not request.REQUEST.has_key("action"):
		raise Exception("action not found") 
	action = json.loads(request.REQUEST["action"])
	res = api.top_action(top_id, action["action"], action["element_type"], action["element_name"], action["attrs"]);
	return res
	
@wrap_json
def task_status(api, request, task_id):
	return api.task_status(task_id, False);

@wrap_json
def permission(api, request, top_id):
	if not request.REQUEST.has_key("permission"):
		raise Exception("permission not found")
	permission = json.loads(request.REQUEST["permission"]); 
	return api.permission_set(top_id, permission["user"], permission["role"]);

@wrap_json
def download_image_uri(api, request, top_id, device):
	return api.top_action(top_id, "download_image", "device", device)

@wrap_json
def download_capture_uri(api, request, top_id, connector, ifname):
	return api.top_action(top_id, "download_capture", "connector", connector, attrs={"iface": ifname, "onlyLatest": request.REQUEST.has_key("onlyLatest") and request.REQUEST["onlyLatest"]})

@wrap_json
def upload_image_uri(api, request, top_id, device):
	redirect = request.build_absolute_uri(reverse('tomato.ajax.use_uploaded_image', kwargs={"top_id": top_id, "device": device})) + "?filename=%(filename)s"
	return api.top_action(top_id, "upload_image_prepare", "device", device, attrs={"redirect": redirect})

@wrap_json
def use_uploaded_image(api, request, top_id, device):
	if not request.REQUEST.has_key("filename"):
		raise Exception("filename not found")
	filename = request.REQUEST["filename"]; 
	return api.top_action(top_id, "upload_image_use", "device", device, attrs={"filename": filename})