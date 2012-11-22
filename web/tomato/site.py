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

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page
from django.http import Http404
from django import forms
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib

class SiteForm(forms.Form):
    name = forms.CharField(max_length=50, help_text="The name of the site. Must be unique to all sites. e.g.: ukl")
    description = forms.CharField(max_length=255, help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
    location = forms.CharField(max_length=255, help_text="e.g.: Germany")
    
class RemoveSiteForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
def is_hostManager(account_info):
    return 'hosts_manager' in account_info['flags']

@cache_page(60)
@wrap_rpc
def index(api, request):
    return render_to_response("admin/site/index.html", {'site_list': api.site_list(), 'hostManager': is_hostManager(api.account_info())})

@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.site_create(formData["name"],formData["description"])
            api.site_modify(formData["name"],{"location": formData["location"]})
            return render_to_response("admin/site/add_success.html", {'name': formData["name"]})
        else:
            return render_to_response("admin/site/form.html", {'form': form, "edit":False})
    else:
        form = SiteForm
        return render_to_response("admin/site/form.html", {'form': form, "edit":False})
    
@wrap_rpc
def remove(api, request):
    if request.method == 'POST':
        form = RemoveSiteForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            api.site_remove(name)
            return render_to_response("admin/site/remove_success.html", {'name': name})
        else:
            name = request.POST['name']
            if name:
                form = RemoveSiteForm()
                form.fields["name"].initial = name
                return render_to_response("admin/site/remove_confirm.html", {'name': name, 'hostManager': is_hostManager(api.account_info()), 'form': form})
            else:
                return render_to_response("main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    
    else:
        name = request.GET['name']
        if name:
            form = RemoveSiteForm()
            form.fields["name"].initial = name
            return render_to_response("admin/site/remove_confirm.html", {'name': name, 'hostManager': is_hostManager(api.account_info()), 'form': form})
        else:
            return render_to_response("main/error.html",{'type':'not enough parameters','text':'No site specified. Have you followed a valid link?'})
    
@wrap_rpc
def edit(api, request):
    if request.method=='POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.site_modify(formData["name"],{'description':formData["description"],'location':formData["location"]})
            return render_to_response("admin/site/edit_success.html", {'name': formData["name"]})
        else:
            name=request.POST["name"]
            if name:
                form.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
                form.fields["name"].help_text=None
                return render_to_response("admin/site/form.html", {'name': name, 'form': form, "edit":True})
            else:
                return render_to_response("main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
            
    else:
        name = request.GET['name']
        if name:
            form = SiteForm(api.site_info(name))
            form.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
            form.fields["name"].help_text=None
            return render_to_response("admin/site/form.html", {'name': name, 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'type':'not enough parameters','text':'No site specified. Have you followed a valid link?'})
