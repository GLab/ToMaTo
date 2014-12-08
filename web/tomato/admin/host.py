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




#TODO: fix add, edit and remove functions


'''
Created on Dec 4, 2014

@author: t-gerhard
'''

from django.shortcuts import render
from django import forms

from tomato.crispy_forms.layout import Layout
from ..admin_common import Buttons
from ..lib import wrap_rpc
from . import add_function, edit_function, remove_function, AddEditForm, RemoveConfirmForm, append_empty_choice, site_name_list


class HostForm(AddEditForm):
    name = forms.CharField(max_length=255,help_text="The host's name. This is also its unique id.")
    address = forms.CharField(max_length=255,help_text="The host's IP address.")
    rpcurl = forms.CharField(max_length=255,help_text="The host's RPC url.")
    site = forms.CharField(max_length=50,help_text="The site this host belongs to.")
    enabled = forms.BooleanField(initial=True, required=False,help_text="Whether this host is enabled.")
    description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
    
    buttons = Buttons.cancel_add
    
    primary_key = "name"
    create_keys = ['name', 'site']
    redirect_after = "tomato.admin.host.info"
    
    def __init__(self, site_namelist, *args, **kwargs):
        super(HostForm, self).__init__(*args, **kwargs)
        self.fields["site"].widget = forms.widgets.Select(choices=site_namelist)
        self.helper.layout = Layout(
            'name',
            'address',
            'rpcurl',
            'site',
            'enabled',
            'description_text',
            self.buttons
        )
        
class AddHostForm(HostForm):
    title = "Add Host"
    formaction = "tomato.admin.host.add"
    formaction_haskeys = False
    def __init__(self, site=None, *args, **kwargs):
        super(AddHostForm, self).__init__(*args, **kwargs)
        if site is not None:
            self.fields['organization'].initial = site
        
    
class EditHostForm(HostForm):
    buttons = Buttons.cancel_save
    title = "Editing Host '%(name)s'"
    formaction = "tomato.admin.host.edit"
    buttons = Buttons.cancel_save
    def __init__(self, *args, **kwargs):
        super(EditHostForm, self).__init__(*args, **kwargs)
        self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["name"].help_text=None
        
    
class RemoveHostForm(RemoveConfirmForm):
    redirect_after_useargs = False
    formaction = "tomato.admin.host.remove"
    redirect_after = "tomato.admin.host.list"
    message="Are you sure you want to remove the host '%(name)s'?"
    title="Remove Host '%(name)s'"
    primary_key = 'name'

    
@wrap_rpc
def list(api, request, site=None, organization=None):    
    organizations = api.organization_list()
    sites = api.site_list()
    hosts = api.host_list(site=site, organization=organization)
    site_description=None
    organization_description=None
    if site:
        site_description=api.site_info(site)['description']
    if organization:
        organization_description = api.organization_info(organization)['description']
    site_map = dict([(s["name"], "%s, %s" % (s["description"] if s["description"] else s["name"], s["location"])) for s in api.site_list()])
    return render(request, "host/list.html", {'host_list': hosts, 'organizations': organizations, 'site_map': site_map, 'sites': sites, 'site': site, 'site_description':site_description, 'organization': organization, 'organization_description': organization_description})

@wrap_rpc
def info(api, request, name):
    host = api.host_info(name)
    site = api.site_info(host["site"])
    organization = api.organization_info(host["organization"])
    return render(request, "host/info.html", {'host': host, 'organization': organization, 'site': site})

    

@wrap_rpc
def add(api, request, site=None):
    return add_function(request,
                        Form=AddHostForm,
                        create_function=api.host_create,
                        modify_function=api.host_modify,
                        clean_formkwargs= ({'site':site} if site is not None else {}),
                        formkwargs = {'site_namelist':append_empty_choice(site_name_list(api))}
                        )

@wrap_rpc
def edit(api, request, name=None):
    return edit_function(request,
                         Form=EditHostForm,
                         modify_function=api.host_modify,
                         primary_value=name,
                         clean_formargs=[api.host_info(name)],
                         formargs = [append_empty_choice(site_name_list(api))]
                         )
    

    
@wrap_rpc
def remove(api, request, name):
    return remove_function(request,
                           Form=RemoveHostForm,
                           delete_function=api.host_remove,
                           primary_value=name
                           )