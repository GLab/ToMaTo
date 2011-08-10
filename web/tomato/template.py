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

from lib import *
import xmlrpclib

class TemplateForm(forms.Form):
	name = forms.CharField(max_length=255)
	type = forms.ChoiceField(choices=[("openvz", "OpenVZ"), ("kvm", "KVM"), ("prog", "Prog")])
	on_hostserver = forms.BooleanField(required=False)
	external_url = forms.URLField(required=False, label="External URL", verify_exists=True)
	notes = forms.CharField(widget=forms.Textarea, required=False)
	
@wrap_rpc
def index(api, request):
	return render_to_response("admin/template_index.html", {'templates': api.template_map()})

@wrap_rpc
def detail(api, request, type, name):
	tpl = api.template_info(type, name)
	form = TemplateForm()
	for f in ["name", "type", "on_hostserver", "external_url", "notes"]:
		form.fields[f].initial = tpl[f]
	form.fields["name"].widget = forms.widgets.HiddenInput()
	form.fields["type"].widget = forms.widgets.HiddenInput()
	return render_to_response("admin/template_detail.html", {'tpl': tpl, 'form': form})

@wrap_rpc
def edit(api, request, type, name):
	if request.method == 'POST':
		form = TemplateForm(request.POST)
		if form.is_valid(): 
			d = form.cleaned_data
			api.template_change(type, name, d)
		else:
			tpl = api.template_info(type, name)
			return render_to_response("admin/template_detail.html", {'tpl': tpl, 'form': form, 'show_form': True})
	return HttpResponseRedirect(reverse('tomato.template.detail', kwargs={"type": type, "name": name}))

@wrap_rpc
def add(api, request):
	if request.method == 'POST':
		form = TemplateForm(request.POST)
		if form.is_valid(): 
			d = form.cleaned_data
			task = api.template_add(d["type"], d["name"], d)
			return render_to_response("admin/template_index.html", {'templates': api.template_map(), "task": task})
	else:
		form = TemplateForm()
		form.fields["name"].initial = "type-version"
	return render_to_response("admin/template_add.html", {"form": form})

@wrap_rpc
def remove(api, request, type, name):
	api.template_remove(type, name)
	return index(request)

@wrap_rpc
def set_default(api, request, type, name):
	api.template_set_default(type, name)
	return index(request)