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

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from django.core.urlresolvers import reverse

from tomato.crispy_forms.layout import Layout
from ..admin_common import Buttons
from ..lib import wrap_rpc, AuthError
from . import add_function, edit_function, remove_function, AddEditForm, RemoveConfirmForm



class OrganizationForm(AddEditForm):
    
    name = forms.CharField(max_length=50, help_text="The name of the organization. Must be unique to all organizations. e.g.: ukl")
    description = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
    homepage_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org")
    image_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org/logo.png")
    description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
    
    buttons = Buttons.cancel_add
    
    primary_key = "name"
    create_keys = ['name', 'description']
    redirect_after = "tomato.admin.organization.info"
    
    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        self.helper.layout = Layout(
            'name',
            'description',
            'homepage_url',
            'image_url',
            'description_text',
            self.buttons
        )
        
class AddOrganizationForm(OrganizationForm):
    title = "Add Organization"
    formaction = "tomato.admin.organization.add"
    formaction_haskeys = False
    def __init__(self, *args, **kwargs):
        super(AddOrganizationForm, self).__init__(*args, **kwargs)
    
class EditOrganizationForm(OrganizationForm):
    buttons = Buttons.cancel_save
    title = "Editing Organization '%(name)s'"
    formaction = "tomato.admin.organization.edit"
    def __init__(self, *args, **kwargs):
        super(EditOrganizationForm, self).__init__(*args, **kwargs)
        self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["name"].help_text=None
        
    
class RemoveOrganizationForm(RemoveConfirmForm):
    redirect_after_useargs = False
    formaction = "tomato.admin.organization.remove"
    redirect_after = "tomato.admin.organization.list"
    message="Are you sure you want to remove the organization '%(name)s'?"
    title="Remove Organization '%(name)s'"
    primary_key = 'name'
        
    

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
    return add_function(request,
                        Form=AddOrganizationForm,
                        create_function=api.organization_create,
                        modify_function=api.organization_modify
                        )

@wrap_rpc
def edit(api, request, name=None):
    return edit_function(request,
                         Form=EditOrganizationForm,
                         modify_function=api.organization_modify,
                         primary_value=name,
                         clean_formargs=[api.organization_info(name)]
                         )
    
@wrap_rpc
def remove(api, request, name):
    return remove_function(request,
                           Form=RemoveOrganizationForm,
                           delete_function=api.organization_remove,
                           primary_value=name
                           )