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
from django.views.decorators.cache import cache_page
from django.http import Http404
from django import forms
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib

class HostForm(forms.Form):
    address = forms.CharField(max_length=255,help_text="The host's IP address. This is also its unique id.")
    site = forms.CharField(max_length=50,help_text="The site this host belongs to.")
    
class EditHostForm(HostForm):
    def __init__(self, *args, **kwargs):
        super(EditHostForm, self).__init__(*args, **kwargs)
        self.fields["address"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["address"].help_text=None
    
class RemoveHostForm(forms.Form):
    address = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
def is_hostManager(account_info):
    return 'hosts_manager' in account_info['flags']
    
def site_name_list(api):
    l = api.site_list()
    res = []
    for site in l:
        res.append((site["name"],site["description"] or site["name"]))
    res.sort()
    return res


@wrap_rpc
def index(api, request):
    netwI_list = api.resource_list('network_instance')
    return render_to_response("admin/external_network_instances/index.html", {'user': api.user, 'netwI_list': netwI_list, 'hostManager': is_hostManager(api.account_info())})

@wrap_rpc
def add(api, request):
    return render_to_response("main/error.html",{'user': api.user, 'type':'not implemented yet'})
   
@wrap_rpc
def remove(api, request):
    return render_to_response("main/error.html",{'user': api.user, 'type':'not implemented yet'})

@wrap_rpc
def edit(api, request):
    return render_to_response("main/error.html",{'user': api.user, 'type':'not implemented yet'})
