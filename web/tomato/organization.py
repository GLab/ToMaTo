# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2012 Integrated Communication Systems Lab, University of Kaiserslautern
#
# This file is part of the ToMaTo project
#
# ToMaTo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import json

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from lib import wrap_rpc, AuthError

from admin_common import BootstrapForm, RemoveConfirmForm, Buttons
from tomato.crispy_forms.layout import Layout
from django.core.urlresolvers import reverse

class OrganizationForm(BootstrapForm):
	name = forms.CharField(max_length=50, help_text="The name of the organization. Must be unique to all organizations. e.g.: ukl")
	description = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
	homepage_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org")
	image_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org/logo.png")
	description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
	buttons = Buttons.cancel_add
	def __init__(self, *args, **kwargs):
		super(OrganizationForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
			'name',
			'description',
			'homepage_url',
			'image_url',
			'description_text',
			self.buttons
		)
	
class EditOrganizationForm(OrganizationForm):
	buttons = Buttons.cancel_save
	def __init__(self, *args, **kwargs):
		super(EditOrganizationForm, self).__init__(*args, **kwargs)
		self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
		self.fields["name"].help_text=None
		self.helper.form_action = reverse(edit, kwargs={"name": self.fields["name"].initial})
	
@wrap_rpc
def list(api, request):
	organizations = api.organization_list()
	sites = api.site_list()
	hosts = api.host_list()
	omap = {}
	for o in organizations:
		o["hosts"] = {"count": 0, "avg_load": 0.0, "avg_availability": 0.0}
		omap[o["name"]] = o
	for h in hosts:
		o = omap[h["organization"]]
		o["hosts"]["count"] += 1
		o["hosts"]["avg_load"] += h["load"] if "host_info" in h else 0.0
		o["hosts"]["avg_availability"] += h["availability"] if "host_info" in h else 0.0
	for o in organizations:
		o["hosts"]["avg_load"] = (o["hosts"]["avg_load"] / o["hosts"]["count"]) if o["hosts"]["count"] else None  
		o["hosts"]["avg_availability"] = (o["hosts"]["avg_availability"] / o["hosts"]["count"]) if o["hosts"]["count"] else None
	organizations.sort(key=lambda o: o["hosts"]["count"], reverse=True)  
	return render(request, "organization/list.html", {'organizations': organizations, 'sites': sites})

@wrap_rpc
def info(api, request, name):
	orga = api.organization_info(name)
	sites = api.site_list(organization=name)
	return render(request, "organization/info.html", {'organization': orga, 'sites': sites})

@wrap_rpc
def add(api, request):
	if request.method == 'POST':
		form = OrganizationForm(request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.organization_create(formData["name"],formData["description"])
			api.organization_modify(formData["name"],{"homepage_url": formData["homepage_url"],
											  'image_url':formData['image_url'],
											  'description_text':formData['description_text']
											  })
			return HttpResponseRedirect(reverse("tomato.organization.info", kwargs={"name": formData["name"]}))
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Organization"})
	else:
		form = OrganizationForm
		return render(request, "form.html", {'form': form, "heading":"Add Organization"})
	
@wrap_rpc
def remove(api, request, name=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.organization_remove(name)
			return HttpResponseRedirect(reverse("tomato.organization.list"))
	form = RemoveConfirmForm.build(reverse("tomato.organization.remove", kwargs={"name": name}))
	return render(request, "form.html", {"heading": "Remove Organization", "message_before": "Are you sure you want to remove the organization '"+name+"'?", 'form': form})
	
@wrap_rpc
def edit(api, request, name=None):
	if request.method=='POST':
		form = EditOrganizationForm(request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.organization_modify(formData["name"],{"description": formData["description"],
													  "homepage_url": formData["homepage_url"],
													  'image_url':formData['image_url'],
													  'description_text':formData['description_text']
													  })
			return HttpResponseRedirect(reverse("tomato.organization.info", kwargs={"name": formData["name"]}))
		else:
			if not name:
				name=request.POST["name"]
			if name:
				form.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
				form.fields["name"].help_text=None
				return render(request, "form.html", {"heading": "Editing Organization '"+name+"'", 'form': form})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
			
	else:
		if name:
			orgaInfo = api.organization_info(name)
			form = EditOrganizationForm(orgaInfo)
			return render(request, "form.html", {"heading": "Editing Organization '"+name+"'", 'form': form})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No organization specified. Have you followed a valid link?'})

@wrap_rpc
def usage(api, request, name): #@ReservedAssignment
	if not api.user:
		raise AuthError()
	usage=api.organization_usage(name)
	return render(request, "main/usage.html", {'usage': json.dumps(usage), 'name': 'Organization %s' % name})
