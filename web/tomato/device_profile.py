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
    label = forms.CharField(max_length=255, help_text="The displayed label for this template")
    diskspace = forms.IntegerField(label="Disk Space (MB)")
    ram = forms.IntegerField(label="RAM (MB)")
    preference = forms.IntegerField(label="Preference", help_text="The profile with the highest preference will be the default profile. An integer number.")

class RePyForm(forms.Form):
    label = forms.CharField(max_length=255, help_text="The displayed label for this template")
    cpus = forms.FloatField(label = "number of CPUs")
    ram = forms.IntegerField(label="RAM (MB)")
    preference = forms.IntegerField(label="Preference", help_text="The profile with the highest preference will be the default profile. An integer number.")

class KVMqmForm(forms.Form):
    label = forms.CharField(max_length=255, help_text="The displayed label for this template")
    diskspace = forms.IntegerField(label="Disk Space (MB)")
    cpus = forms.IntegerField(label="number of CPUs")
    ram = forms.IntegerField(label="RAM (MB)")
    preference = forms.IntegerField(label="Preference", help_text="The profile with the highest preference will be the default profile. An integer number.")
    
class AddOpenVZForm(OpenVZForm):
    name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all OpenVZ templates. Cannot be changed. Not displayed.")
    def __init__(self, *args, **kwargs):
        super(AddOpenVZForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['name', 'label', 'diskspace', 'ram', 'preference']
    
class AddRePyForm(RePyForm):
    name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all RePy templates. Cannot be changed. Not displayed.")
    def __init__(self, *args, **kwargs):
        super(AddRePyForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['name', 'label', 'cpus', 'ram', 'preference']
    
class AddKVMqmForm(KVMqmForm):
    name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all KVM templates. Cannot be changed. Not displayed.")
    def __init__(self, *args, **kwargs):
        super(AddKVMqmForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['name', 'label', 'diskspace', 'cpus', 'ram', 'preference']
    
class EditOpenVZForm(OpenVZForm):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
class EditRePyForm(RePyForm):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
class EditKVMqmForm(KVMqmForm):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
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
        form = AddOpenVZForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('profile',{'name':formData['name'],'diskspace':formData['diskspace'],'ram':formData['ram'],'label':formData['label'],'tech':'openvz','preference':formData['preference']})
            return render_to_response("admin/device_profile/add_success.html", {'label': formData["label"],'tech':'openvz'})
        else:
            return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"openvz"})
    else:
        form = AddOpenVZForm
        return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"openvz"})
    
@wrap_rpc
def add_kvmqm(api, request):
    if request.method == 'POST':
        form = AddKVMqmForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('profile',{'name':formData['name'],'diskspace':formData['diskspace'],'ram':formData['ram'],'cpus':formData['cpus'],'label':formData['label'],'tech':'kvmqm','preference':formData['preference']})
            return render_to_response("admin/device_profile/add_success.html", {'label': formData["label"], 'tech':'kvmqm'})
        else:
            return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"kvmqm"})
    else:
        form = AddKVMqmForm
        return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"kvmqm"})
    
@wrap_rpc
def add_repy(api, request):
    if request.method == 'POST':
        form = AddRePyForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('profile',{'name':formData['name'],'ram':formData['ram'],'cpus':formData['cpus'],'label':formData['label'],'tech':'repy','preference':formData['preference']})
            return render_to_response("admin/device_profile/add_success.html", {'label': formData["label"], 'tech':'repy'})
        else:
            return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"repy"})
    else:
        form = AddRePyForm
        return render_to_response("admin/device_profile/form.html", {'form': form, "edit":False, 'tech':"repy"})
    
@wrap_rpc
def remove(api, request):
    if request.method == 'POST':
        form = RemoveResourceForm(request.POST)
        if form.is_valid():
            res_id = form.cleaned_data["res_id"]
            if api.resource_info(res_id) and api.resource_info(res_id)['type'] == 'profile':
                label = api.resource_info(res_id)['attrs']['label']
                tech = api.resource_info(res_id)['attrs']['tech']
                api.resource_remove(res_id)
                return render_to_response("admin/device_profile/remove_success.html", {'label':label, 'tech':tech})
            else:
                return render_to_response("main/error.html",{'type':'invalid id','text':'There is no device profile with id '+res_id})
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
def add(api, request):
    return render_to_response("admin/device_profile/add_unspecified.html",{})

@wrap_rpc
def edit_kvmqm(api, request):
    if request.method=='POST':
        form = EditKVMqmForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if api.resource_info(formData['res_id'])['type'] == 'profile' and api.resource_info(formData['res_id'])['attrs']['tech'] == 'kvmqm':
                api.resource_modify(formData["res_id"],{'diskspace':formData['diskspace'],'ram':formData['ram'],'cpus':formData['cpus'],'label':formData['label'],'tech':'kvmqm','preference':formData['preference']})
                return render_to_response("admin/device_profile/edit_success.html", {'label': formData["label"],'tech':'kvmqm'})
            else:
                return render_to_response("main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no kvmqm device profile.'})
        else:
            name="ERROR"
            return render_to_response("admin/device_profile/form.html", {'label': name, 'tech':'kvmqm', 'form': form, "edit":True})
    else:
        res_id = request.GET['id']
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            form = EditKVMqmForm(origData)
            return render_to_response("admin/device_profile/form.html", {'label': res_info['attrs']['label'], 'tech':'kvmqm', 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})

@wrap_rpc
def edit_openvz(api, request):
    if request.method=='POST':
        form = EditOpenVZForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if api.resource_info(formData['res_id'])['type'] == 'profile' and api.resource_info(formData['res_id'])['attrs']['tech'] == 'openvz':
                api.resource_modify(formData["res_id"],{'diskspace':formData['diskspace'],'ram':formData['ram'],'label':formData['label'],'tech':'openvz','preference':formData['preference']})
                return render_to_response("admin/device_profile/edit_success.html", {'label': formData["label"],'tech':'openvz'})
            else:
                return render_to_response("main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no openvz device profile.'})
        else:
            name="ERROR"
            return render_to_response("admin/device_profile/form.html", {'label': name, 'tech':'openvz', 'form': form, "edit":True})
    else:
        res_id = request.GET['id']
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            form = EditOpenVZForm(origData)
            return render_to_response("admin/device_profile/form.html", {'label': res_info['attrs']['label'], 'tech':'openvz', 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})

@wrap_rpc
def edit_repy(api, request):
    if request.method=='POST':
        form = EditRePyForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if api.resource_info(formData['res_id'])['type'] == 'profile' and api.resource_info(formData['res_id'])['attrs']['tech'] == 'repy':
                api.resource_modify(formData["res_id"],{'ram':formData['ram'],'cpus':formData['cpus'],'label':formData['label'],'tech':'repy','preference':formData['preference']})
                return render_to_response("admin/device_profile/edit_success.html", {'label': formData["label"],'tech':'repy'})
            else:
                return render_to_response("main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no repy device profile.'})
        else:
            name="ERROR"
            return render_to_response("admin/device_profile/form.html", {'label': name, 'tech':'repy', 'form': form, "edit":True})
    else:
        res_id = request.GET['id']
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            form = EditRePyForm(origData)
            return render_to_response("admin/device_profile/form.html", {'label': res_info['attrs']['label'], 'tech':'repy', 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})

