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

class TemplateForm(forms.Form):
	name = forms.CharField(max_length=255)
	type = forms.ChoiceField(choices=[("openvz", "OpenVZ"), ("kvm", "KVM")])
	url = forms.URLField(label="Download URL", verify_exists=True)

@wrap_rpc
def index(api, request):
	return render_to_response("admin/template_index.html", {'templates': api.template_list("*")})

@wrap_rpc
def add(api, request):
	if request.method == 'POST':
		form = TemplateForm(request.POST)
		if form.is_valid(): 
			d = form.cleaned_data
			task = api.template_add(d["name"], d["type"], d["url"])
			return render_to_response("admin/template_index.html", {'templates': api.template_list("*"), "task": task})
	else:
		form = TemplateForm()
	return render_to_response("admin/template_add.html", {"form": form})

@wrap_rpc
def remove(api, request, name):
	api.template_remove(name)
	return index(request)

@wrap_rpc
def set_default(api, request, type, name):
	api.template_set_default(type, name)
	return index(request)