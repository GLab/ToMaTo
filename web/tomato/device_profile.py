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
from django.http import Http404
from django import forms
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib

class OpenVZForm(forms.Form):
    name = forms.CharField(max_length=50,label="Internal Name")
    label = forms.CharField(max_length=255)
    diskspace = forms.IntegerField(label="Disk Space")
    ram = forms.IntegerField(label="RAM")
    preference = forms.IntegerField(label="Preference")

class RePyForm(forms.Form):
    name = forms.CharField(max_length=50,label="Internal Name")
    label = forms.CharField(max_length=255)
    ram = forms.IntegerField(label="RAM")
    cpus = forms.FloatField(label = "no. of CPUs")
    preference = forms.IntegerField(label="Preference")

class KVMqmForm(forms.Form):
    name = forms.CharField(max_length=50,label="Internal Name")
    label = forms.CharField(max_length=255)
    diskspace = forms.IntegerField(label="Disk Space")
    ram = forms.IntegerField(label="RAM")
    cpus = forms.IntegerField(label="no. of CPUs")
    preference = forms.IntegerField(label="Preference")
    
class RemoveResourceForm(forms.Form):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
def is_hostManager(account_info):
    return 'hosts_manager' in account_info['flags']

@wrap_rpc
def index(api, request):
    reslist = api.resource_list()
    profile_kvmqm_list = []
    profile_repy_list = []
    profile_openvz_list = []
    for res in reslist:
        if res['type'] == 'profile':
            if res['attrs']['tech'] == 'kvmqm':
                profile_kvmqm_list.append(res)
            else:
                if res['attrs']['tech'] == 'openvz':
                    profile_openvz_list.append(res)
                else:
                    profile_repy_list.append(res)
        
    return render_to_response("admin/device_profile/index.html", {'profile_kvmqm_list': profile_kvmqm_list, 'profile_openvz_list': profile_openvz_list, 'profile_repy_list': profile_repy_list, 'hostManager': is_hostManager(api.account_info())})


@wrap_rpc
def add_openvz(api, request):
    if request.method == 'POST':
        form = OpenVZForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('profile',{'name':formData['name'],'diskspace':formData['diskspace'],'ram':formData['ram'],'label':formData['label'],'tech':'openvz','preference':formData['preference']})
            return render_to_response("admin/device_profile/add_success.html", {'label': formData["label"],'tech':'openvz'})
        else:
            return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"openvz"})
    else:
        form = OpenVZForm
        return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"openvz"})
    
@wrap_rpc
def add_kvmqm(api, request):
    if request.method == 'POST':
        form = KVMqmForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('profile',{'name':formData['name'],'diskspace':formData['diskspace'],'ram':formData['ram'],'cpus':formData['cpus'],'label':formData['label'],'tech':'kvmqm','preference':formData['preference']})
            return render_to_response("admin/device_profile/add_success.html", {'label': formData["label"], 'tech':'kvmqm'})
        else:
            return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"kvmqm"})
    else:
        form = KVMqmForm
        return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"kvmqm"})
    
@wrap_rpc
def add_repy(api, request):
    if request.method == 'POST':
        form = RePyForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('profile',{'name':formData['name'],'ram':formData['ram'],'cpus':formData['cpus'],'label':formData['label'],'tech':'repy','preference':formData['preference']})
            return render_to_response("admin/device_profile/add_success.html", {'label': formData["label"], 'tech':'repy'})
        else:
            return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"repy"})
    else:
        form = RePyForm
        return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"repy"})
    
@wrap_rpc
def remove(api, request):
    if request.method == 'POST':
        form = RemoveResourceForm(request.POST)
        if form.is_valid():
            res_id = form.cleaned_data["res_id"]
            label = api.resource_info(res_id)['attrs']['label']
            tech = api.resource_info(res_id)['attrs']['tech']
            api.resource_remove(res_id)
            return render_to_response("admin/device_profile/remove_success.html", {'label':label, 'tech':tech})
        else:
            res_id = request.POST['res_id']
            form = RemoveResourceForm()
            form.fields["res_id"].initial = res_id
            return render_to_response("admin/device_profile/remove_confirm.html", {'label': api.resource_info(res_id)['attrs']['label'], 'tech': api.resource_info(res_id)['attrs']['tech'], 'hostManager': is_hostManager(api.account_info()), 'form': form})
    
    else:
        res_id = request.GET['id']
        form = RemoveResourceForm()
        form.fields["res_id"].initial = res_id
        return render_to_response("admin/device_profile/remove_confirm.html", {'label': api.resource_info(res_id)['attrs']['label'], 'tech': api.resource_info(res_id)['attrs']['tech'], 'hostManager': is_hostManager(api.account_info()), 'form': form})
    

@wrap_rpc
def edit(api, request):
    return index(api,request)

