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

class SpecialFeatureGroupForm(forms.Form):
	feature_type = forms.CharField(label="Feature type", max_length=50)
	group_name = forms.CharField(label="Group name", max_length=50)
	max_devices = forms.IntegerField(label="Maximal devices", required=False)
	avoid_duplicates = forms.BooleanField(label="Avoid duplicates", initial=False, required=False)

@wrap_rpc
def index(api, request):
	return render_to_response("admin/special_features_index.html", {'list': api.special_features()})

@wrap_rpc
def add_host(api, request, hostname):
	(type, group) = request.REQUEST["typegroup"].split(":")
	bridge = request.REQUEST["bridge"]
	api.special_features_add(hostname, type, group, bridge)
	import host
	return host.detail(request, hostname)
	
@wrap_rpc
def remove_host(api, request, type, group, hostname):
	api.special_features_remove(hostname, type, group)
	import host
	return host.detail(request, hostname)
	
@wrap_rpc
def add_group(api, request):
	if request.method == 'POST':
		form = SpecialFeatureGroupForm(request.POST)
		if form.is_valid():
			d=form.cleaned_data
			params={"avoid_duplicates": d["avoid_duplicates"]}
			if d["max_devices"]:
				params["max_devices"] = d["max_devices"]
			print d
			api.special_feature_group_add(d["feature_type"], d["group_name"], params)		
			return index(request)
	else:
		form = SpecialFeatureGroupForm()
	return render_to_response("admin/generic_form.html", {'type': "special feature", 'form': form})
	
@wrap_rpc
def remove_group(api, request, type, group):
	api.special_features_group_remove(type, group)
	return index(request)
	
@wrap_rpc
def change_group(api, request, type, group):
	if request.method == 'POST':
		form = SpecialFeatureGroupForm(request.POST)
		if form.is_valid():
			d=form.cleaned_data
			params={"avoid_duplicates": d["avoid_duplicates"]}
			if d["max_devices"]:
				params["max_devices"] = d["max_devices"]
			print d
			api.special_feature_group_change(d["feature_type"], d["group_name"], params)		
			return index(request)
	else:
		for sf in api.special_features():
			if sf["type"] == type and sf["name"] == group:
				form = SpecialFeatureGroupForm({"feature_type": sf["type"], "group_name": sf["name"], "max_devices": (sf["max_devices"] if sf["max_devices"] else ""), "avoid_duplicates": sf["avoid_duplicates"]})
		form.fields["feature_type"].widget = forms.widgets.HiddenInput()
		form.fields["group_name"].widget = forms.widgets.HiddenInput()
	return render_to_response("admin/generic_form.html", {'type': "special feature", 'name': "%s (%s)" % (type, group), 'form': form})
	