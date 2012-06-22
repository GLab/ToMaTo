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
from django import forms
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory

from lib import *
import xmlrpclib

class ProfileForm(forms.Form):
	name = forms.CharField(max_length=255)
	type = forms.ChoiceField(choices=[("openvz", "OpenVZ"), ("kvm", "KVM"), ("prog", "Prog")])

class AttrForm(forms.Form):
	name = forms.CharField(max_length=255, required=False)
	value = forms.CharField(max_length=255, required=False)

AttrFormSet = formset_factory(AttrForm, extra=3)	
	
@wrap_rpc
def index(api, request):
	return render_to_response("admin/device_profile_index.html", {'profiles': api.device_profile_map()})

@wrap_rpc
def detail(api, request, type, name, task=None):
	profile = api.device_profile_info(type, name)
	form = AttrFormSet(initial=[{"name": name, "value": value} for (name, value) in profile["attrs"].iteritems()])
	return render_to_response("admin/device_profile_detail.html", {'profile': profile, 'form': form})

@wrap_rpc
def edit(api, request, type, name):
	if request.method == 'POST':
		form = AttrFormSet(request.POST)
		print form.is_valid()
		if form.is_valid():
			attrs = dict([(f["name"], f["value"]) for f in filter(lambda x: x.get("name"), form.cleaned_data)])
			print attrs
			task = api.device_profile_change(type, name, attrs)
			return detail(request, type, name, task=task) 
		else:
			profile = api.device_profile_info(type, name)
			return render_to_response("admin/device_profile_detail.html", {'profile': profile, 'form': form, 'show_form': True})
	return HttpResponseRedirect(reverse('tomato.device_profile.detail', kwargs={"type": type, "name": name}))

@wrap_rpc
def add(api, request):
	if request.method == 'POST':
		form = ProfileForm(request.POST)
		if form.is_valid(): 
			d = form.cleaned_data
			task = api.device_profile_add(d["type"], d["name"], {})
			return detail(request, d["type"], d["name"], task)
	else:
		form = ProfileForm()
	return render_to_response("admin/device_profile_add.html", {"form": form})

@wrap_rpc
def remove(api, request, type, name):
	api.device_profile_remove(type, name)
	return index(request)

@wrap_rpc
def set_default(api, request, type, name):
	api.device_profile_set_default(type, name)
	return index(request)