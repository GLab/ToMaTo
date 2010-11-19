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

from lib import *
import xmlrpclib

@wrap_rpc
def index(api, request):
	return render_to_response("admin/host_index.html", {'host_list': api.host_list()})

@wrap_rpc
def detail(api, request, hostname):
	return render_to_response("admin/host_detail.html", {'host': api.host_info(hostname)})

@wrap_rpc
def edit(api, request):
	host = None
	if request.REQUEST.has_key("hostname"):
		hostname = request.REQUEST["hostname"]
		host = api.host_info(hostname)
	if not request.REQUEST.has_key("action"):
		return render_to_response("admin/host_edit.html", {"host": host})
	hostname=request.REQUEST["hostname"]
	group=request.REQUEST["group"]
	enabled=request.REQUEST.has_key("enabled")
	vmid_start=request.REQUEST["vmid_start"]
	vmid_count=request.REQUEST["vmid_count"]
	port_start=request.REQUEST["port_start"]
	port_count=request.REQUEST["port_count"]
	bridge_start=request.REQUEST["bridge_start"]
	bridge_count=request.REQUEST["bridge_count"]
	action = request.REQUEST["action"] 
	if action=="add":
		task_id = api.host_add(hostname, group, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count)
		return render_to_response("admin/host_edit.html", {"task_id": task_id, "hostname": hostname})
	else:
		api.host_change(hostname, group, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count)
		return detail(request, hostname)

@wrap_rpc
def check(api, request, hostname):
	task = api.host_check(hostname)
	return render_to_response("admin/host_index.html", {'host_list': api.host_list(), 'task': task, 'taskname': "Checking host %s" % hostname})

@wrap_rpc
def debug(api, request, hostname):
	debug_info = api.host_debug(hostname)
	debug = [(k, debug_info[k]) for k in debug_info]
	return render_to_response("admin/host_debug.html", {"host_name": hostname, "debug": debug})

@wrap_rpc
def remove(api, request, hostname):
	api.host_remove(hostname)
	return index(request)

@wrap_rpc
def special_feature_add(api, request, hostname):
	type = request.REQUEST["type"]
	group = request.REQUEST["group"]
	bridge = request.REQUEST["bridge"]		
	api.special_features_add(hostname, type, group, bridge)
	return detail(request, hostname)

@wrap_rpc
def special_feature_remove(api, request, hostname):
	type = request.REQUEST["type"]
	group = request.REQUEST["group"]
	api.special_features_remove(hostname, type, group)
	return detail(request, hostname)