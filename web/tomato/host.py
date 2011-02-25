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
from django import forms

from lib import *
import xmlrpclib

class HostForm(forms.Form):
	name = forms.CharField(max_length=255)
	group = forms.CharField(max_length=10)
	enabled = forms.BooleanField(required=False)
	vmid_start = forms.IntegerField(label="VMID range start", initial=1000, min_value=1000)
	vmid_count = forms.IntegerField(label="VMID range count", initial=200, min_value=0)
	port_start = forms.IntegerField(label="Port range start", initial=7000, min_value=1025, max_value=30000)
	port_count = forms.IntegerField(label="Port range count", initial=1000, min_value=0, max_value=5000)
	bridge_start = forms.IntegerField(label="Bridge range start", initial=1000)
	bridge_count = forms.IntegerField(label="Bridge range count", initial=1000, min_value=0)

@wrap_rpc
def index(api, request):
	return render_to_response("admin/host_index.html", {'host_list': api.host_list()})

@wrap_rpc
def detail(api, request, hostname):
	return render_to_response("admin/host_detail.html", {'host': api.host_info(hostname), 'special_features': api.special_features()})

@wrap_rpc
def edit(api, request, hostname):
	if request.method == 'POST':
		form = HostForm(request.POST)
		if form.is_valid(): 
			if not hostname:
				d = form.cleaned_data
				task_id = api.host_add(d["name"], d["group"], d["enabled"], d["vmid_start"], d["vmid_count"], d["port_start"], d["port_count"], d["bridge_start"], d["bridge_count"])
				return render_to_response("admin/host_edit.html", {"task_id": task_id, "hostname": d["name"]})
			else:
				d = form.cleaned_data
				api.host_change(hostname, d["group"], d["enabled"], d["vmid_start"], d["vmid_count"], d["port_start"], d["port_count"], d["bridge_start"], d["bridge_count"])
				return detail(request, hostname)
	else:
		if hostname:
			host_info = api.host_info(hostname)
			form = HostForm(host_info)
			form.fields["name"].widget = forms.widgets.HiddenInput()
		else:
			form = HostForm()
	return render_to_response("admin/host_edit.html", {"form": form, "edit_host": hostname})
		
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