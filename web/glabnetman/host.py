# -*- coding: utf-8 -*-

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
	return render_to_response("admin/host_index.html", {'host_list': api.host_list()})
remove=wrap_rpc(remove)