# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2014 Integrated Communication Systems Lab, University of Kaiserslautern
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

'''
Created on Dec 4, 2014

@author: t-gerhard
'''

from django.shortcuts import render
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from tomato.crispy_forms.layout import Layout
from ..admin_common import Buttons
from ..lib import wrap_rpc
from . import AddEditForm, RemoveConfirmForm



class OrganizationForm(AddEditForm):
    
    name = forms.CharField(max_length=50, help_text="The name of the organization. Must be unique to all organizations. e.g.: ukl")
    label = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
    homepage_url = forms.URLField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org")
    image_url = forms.URLField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org/logo.png")
    description = forms.CharField(widget = forms.Textarea, label="Description", required=False)
    
    buttons = Buttons.cancel_add

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        self.helper.layout = Layout(
            'name',
            'label',
            'homepage_url',
            'image_url',
            'description',
            self.buttons
        )

    def get_redirect_after(self):
        return HttpResponseRedirect(reverse("tomato.admin.organization.info", kwargs={"name": self.cleaned_data['name']}))

        
class AddOrganizationForm(OrganizationForm):
    title = "Add Organization"

    def __init__(self, *args, **kwargs):
        super(AddOrganizationForm, self).__init__(*args, **kwargs)

    def submit(self, api):
      formData = self.cleaned_data
      api.organization_create(formData['name'], formData['label'],
											{k: v for k, v in formData.iteritems() if k not in ('name', 'label')})

class EditOrganizationForm(OrganizationForm):
    buttons = Buttons.cancel_save
    title = "Editing Organization '%(name)s'"
    formaction = "tomato.admin.organization.edit"
    def __init__(self, *args, **kwargs):
        super(EditOrganizationForm, self).__init__(*args, **kwargs)
        self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["name"].help_text=None

    def submit(self, api):
      formData = self.cleaned_data
      api.organization_modify(formData['name'],
			                         {k: v for k, v in formData.iteritems() if k not in ('name',)})

    
class RemoveOrganizationForm(RemoveConfirmForm):
    message="Are you sure you want to remove the organization '%(name)s'?"
    title="Remove Organization '%(name)s'"

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
    smap = {}
    hosts = api.host_list(organization=name)
    for site in sites:
        if site.get('geolocation', None):
            if site['geolocation']['longitude'] > 0:
                site['geolocation']['longitude'] = str(site['geolocation']['longitude']) + 'E'
            else:
                site['geolocation']['longitude'] = str(-site['geolocation']['longitude']) + 'W'
            if site['geolocation']['latitude'] > 0:
                site['geolocation']['latitude'] = str(site['geolocation']['latitude']) + 'N'
            else:
                site['geolocation']['latitude'] = str(-site['geolocation']['latitude']) + 'S'

        smap[site['name']] = site
        site['hosts'] = {"count": 0, "avg_load": 0.0, "avg_availability": 0.0}
    orga['hosts'] = {"count": 0, "avg_load": 0.0, "avg_availability": 0.0}
    for h in hosts:
        s = smap[h['site']]
        s["hosts"]["count"] += 1
        s["hosts"]["avg_load"] += h["load"] if "host_info" in h else 0.0
        s["hosts"]["avg_availability"] += h["availability"] if "host_info" in h else 0.0
        orga["hosts"]["count"] += 1
        orga["hosts"]["avg_load"] += h["load"] if "host_info" in h else 0.0
        orga["hosts"]["avg_availability"] += h["availability"] if "host_info" in h else 0.0
    for s in sites:
        s["hosts"]["avg_load"] = (s["hosts"]["avg_load"] / s["hosts"]["count"]) if s["hosts"]["count"] else None
        s["hosts"]["avg_availability"] = (s["hosts"]["avg_availability"] / s["hosts"]["count"]) if s["hosts"]["count"] else None
    orga["hosts"]["avg_load"] = (orga["hosts"]["avg_load"] / orga["hosts"]["count"]) if orga["hosts"]["count"] else None
    orga["hosts"]["avg_availability"] = (orga["hosts"]["avg_availability"] / orga["hosts"]["count"]) if orga["hosts"]["count"] else None

    return render(request, "organization/info.html", {'organization': orga, 'sites': sites})

@wrap_rpc
def add(api, request):
	if request.method == 'POST':
		form = AddOrganizationForm(data=request.POST)
		if form.is_valid():
			form.submit(api)
			return form.get_redirect_after()
		else:
			return form.create_response(request)
	else:
		form = AddOrganizationForm()
		return form.create_response(request)


@wrap_rpc
def edit(api, request, name=None):
	if request.method == 'POST':
		form = EditOrganizationForm(data=request.POST)
		if form.is_valid():
			form.submit(api)
			return form.get_redirect_after()
		else:
			return form.create_response(request)
	else:
		form = EditOrganizationForm(data=api.organization_info(name))
		return form.create_response(request)
    
@wrap_rpc
def remove(api, request, name):
	if request.method == 'POST':
		form = RemoveOrganizationForm(name=name)
		if form.is_valid():
			api.host_remove(name)
			return HttpResponseRedirect('tomato.admin.organization.list')
	form = RemoveOrganizationForm(name=name)
	return form.create_response(request)