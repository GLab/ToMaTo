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
from django.contrib.messages import api

class ExternalNetworkForm(forms.Form):
	type = forms.CharField(label="Type", max_length=50)
	group = forms.CharField(label="Group", max_length=50)
	max_devices = forms.IntegerField(label="Maximal devices", required=False)
	avoid_duplicates = forms.BooleanField(label="Avoid duplicates", initial=False, required=False)

@wrap_rpc
def index(api, request):
	return render_to_response("admin/external_networks_index.html", {'list': api.external_networks()})

@wrap_rpc
def add_bridge(api, request, hostname):
	(type, group) = request.REQUEST["typegroup"].split(":")
	bridge = request.REQUEST["bridge"]
	api.external_network_bridge_add(hostname, type, group, bridge)
	import host
	return host.detail(request, hostname)
	
@wrap_rpc
def remove_bridge(api, request, type, group, hostname):
	api.external_network_bridge_remove(hostname, type, group)
	import host
	return host.detail(request, hostname)
	
@wrap_rpc
def add(api, request):
	if request.method == 'POST':
		form = ExternalNetworkForm(request.POST)
		if form.is_valid():
			d=form.cleaned_data
			params={"avoid_duplicates": d["avoid_duplicates"]}
			if d["max_devices"]:
				params["max_devices"] = d["max_devices"]
			print d
			api.external_network_add(d["type"], d["group"], params)		
			return index(request)
	else:
		form = ExternalNetworkForm()
	return render_to_response("admin/generic_form.html", {'type': "external network", 'form': form})
	
@wrap_rpc
def remove(api, request, type, group):
	api.external_network_remove(type, group)
	return index(request)
	
@wrap_rpc
def change(api, request, type, group):
	if request.method == 'POST':
		form = ExternalNetworkForm(request.POST)
		if form.is_valid():
			d=form.cleaned_data
			params={"avoid_duplicates": d["avoid_duplicates"]}
			if d["max_devices"]:
				params["max_devices"] = d["max_devices"]
			print d
			api.external_network_change(d["type"], d["group"], params)		
			return index(request)
	else:
		for en in api.external_networks():
			if en["type"] == type and en["group"] == group:
				form = ExternalNetworkForm({"type": en["type"], "group": en["group"], "max_devices": (en["max_devices"] if en["max_devices"] else ""), "avoid_duplicates": en["avoid_duplicates"]})
		form.fields["type"].widget = forms.widgets.HiddenInput()
		form.fields["group"].widget = forms.widgets.HiddenInput()
	return render_to_response("admin/generic_form.html", {'type': "external network", 'name': "%s (%s)" % (type, group), 'form': form})
	