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

class HostForm(forms.Form):
    address = forms.CharField(max_length=255)
    site = forms.CharField(max_length=50)
    
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
	return render_to_response("admin/host/index.html", {'host_list': api.host_list(), 'hostManager': is_hostManager(api.account_info())})

@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = HostForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.host_create(formData["address"],formData["site"])
            return render_to_response("admin/host/add_success.html", {'address': formData["address"]})
        else:
            form = HostForm()
            form.fields["site"].widget = forms.widgets.Select(choices=site_name_list(api))
            return render_to_response("admin/host/form.html", {'form': form, 'action':request.path,"edit":False})
    else:
        form = HostForm()
        form.fields["site"].widget = forms.widgets.Select(choices=site_name_list(api))
        return render_to_response("admin/host/form.html", {'form': form, 'action':request.path,"edit":False})
   
@wrap_rpc
def remove(api, request):
    if request.method == 'POST':
        form = RemoveHostForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data["address"]
            api.host_remove(address)
            return render_to_response("admin/host/remove_success.html", {'address': address})
    else:
        address=request.GET['address']
        if address:
            form = RemoveHostForm()
            return render_to_response("admin/host/remove_confirm.html", {'address': address, 'hostManager': is_hostManager(api.account_info()), 'form': form, 'action':request.path})

@wrap_rpc
def edit(api, request):
    if request.method=='POST':
        form = HostForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.host_modify(formData["address"],{'site':formData["site"]})
            return render_to_response("admin/host/edit_success.html", {'address': formData["address"]})
    else:
        address = request.GET['address']
        if address:
            hostinfo=api.host_info(address)
            form = HostForm(hostinfo)
            form.fields["address"].widget=forms.TextInput(attrs={'disabled':'disabled'})
            form.fields["site"].widget = forms.widgets.Select(choices=site_name_list(api))
            form.fields["site"].initial = hostinfo["site"]
            return render_to_response("admin/host/form.html", {'address': address, 'form': form, 'action':request.path, "edit":True})