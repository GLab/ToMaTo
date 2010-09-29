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

def index(api, request):
	return render_to_response("admin/host_index.html", {'host_list': api.host_list()})
index=wrap_rpc(index)

def add(api, request):
	if not request.REQUEST.has_key("hostname"):
		return render_to_response("admin/host_add.html")
	hostname=request.REQUEST["hostname"]
	group=request.REQUEST["group"]
	public_bridge=request.REQUEST["public_bridge"]
	task_id = api.host_add(hostname, group, public_bridge)
	return render_to_response("admin/host_add.html", {"task_id": task_id, "hostname": hostname})
add=wrap_rpc(add)

def debug(api, request, hostname):
	debug_info = api.host_debug(hostname)
	debug = [(k, debug_info[k]) for k in debug_info]
	return render_to_response("admin/host_debug.html", {"host_name": hostname, "debug": debug})
debug=wrap_rpc(debug)

def remove(api, request, hostname):
	api.host_remove(hostname)
	return index(request)
remove=wrap_rpc(remove)