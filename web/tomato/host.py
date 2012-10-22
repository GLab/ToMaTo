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

class AddHostForm(forms.Form):
    address = forms.CharField(max_length=255)
    site = forms.CharField(max_length=50)
    
def is_hostManager(account_info):
	return 'hosts_manager' in account_info['flags']
    
def site_name_list(api):
    l = api.site_list()
    res = []
    for site in l:
        res.append(object)(site["name"])
    res,sort()
    return res

@wrap_rpc
def index(api, request):
	return render_to_response("admin/host/index.html", {'host_list': api.host_list(), 'hostManager': is_hostManager(api.account_info())})

@wrap_rpc
def add(api, request):
    #
    # NOT FULLY IMPLEMENTED
    # check for duplicates
    # length of form fields (AddHostForm)
    #
    if request.method == 'POST':
        form = AddHostForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if formData["address"]: #At this point, check if trying to add a duplicate. (This is a dummy!)
                api.host_create(formData["address"],formData["site"])
                return render_to_response("admin/host/add_success.html", {'address': formData["site"]})
            else:
                return render_to_response("admin/host/add_form.html", {'form': form, 'action':request.path, 'site_list': site_name_list(api)})
        else:
            return render_to_response("admin/host/add_form.html", {'form': form, 'action':request.path, 'site_list': site_name_list(api)})
    else:
        form = AddHostForm
        return render_to_response("admin/host/add_form.html", {'form': form, 'action':request.path, 'site_list': site_name_list(api)})
   
@wrap_rpc
def remove(api, request):
    #
    #
    #   DUMMY
    #
    #
    hostManager = True
    return render_to_response("admin/host/index.html", {'host_list': api.host_list(), 'hostManager': hostManager})

@wrap_rpc
def edit(api, request):
    #
    #
    #   DUMMY
    #
    #
    hostManager = True
    return render_to_response("admin/host/index.html", {'host_list': api.host_list(), 'hostManager': hostManager})