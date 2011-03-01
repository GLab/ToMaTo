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
import simplejson as json;

from lib import *

@wrap_json
def modify(api, request, top_id):
	if not request.REQUEST.has_key("mods"):
		raise Exception("mods not found") 
	mods = json.loads(request.REQUEST["mods"])
	#print mods
	res = api.top_modify(top_id, mods, True)
	return res["output"]

@wrap_json
def info(api, request, top_id):
	res = api.top_info(top_id);
	return res

@wrap_json
def action(api, request, top_id):
	if not request.REQUEST.has_key("action"):
		raise Exception("action not found") 
	action = json.loads(request.REQUEST["action"])
	res = api.top_action(top_id, action["element_type"], action["element_name"], action["action"], action["attrs"]);
	return res
	
@wrap_json
def task_status(api, request, task_id):
	return api.task_status(task_id);

@wrap_json
def permission(api, request, top_id):
	if not request.REQUEST.has_key("permission"):
		raise Exception("permission not found")
	permission = json.loads(request.REQUEST["permission"]); 
	return api.permission_set(top_id, permission["user"], permission["role"]);
