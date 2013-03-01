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
from admin_common import RemoveResourceForm, is_hostManager

class ProfileForm(forms.Form):
    label = forms.CharField(max_length=255, help_text="The displayed label for this template")
    ram = forms.IntegerField(label="RAM (MB)")
    preference = forms.IntegerField(label="Preference", help_text="The profile with the highest preference will be the default profile. An integer number.")
    restricted = forms.BooleanField(label="Restricted", help_text="Restrict usage of this template to administrators", required=False)
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    tech = forms.CharField(max_length=50, widget=forms.HiddenInput)
    cpus = forms.FloatField(label = "number of CPUs")


class EditOpenVZForm(ProfileForm):
    diskspace = forms.IntegerField(label="Disk Space (MB)")
    def __init__(self, *args, **kwargs):
        super(EditOpenVZForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['res_id', 'tech', 'label', 'cpus', 'diskspace', 'ram', 'restricted', 'preference']

class EditRePyForm(ProfileForm):
    def __init__(self, *args, **kwargs):
        super(EditRePyForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['res_id', 'tech', 'label', 'cpus', 'ram', 'restricted', 'preference']

class EditKVMqmForm(ProfileForm):
    diskspace = forms.IntegerField(label="Disk Space (MB)")
    def __init__(self, *args, **kwargs):
        super(EditKVMqmForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['res_id', 'tech', 'label', 'diskspace', 'cpus', 'ram', 'restricted', 'preference']
    
    
class AddProfileForm(ProfileForm):
    tech = forms.ChoiceField(label="Tech",choices=[('kvmqm','kvmqm'), ('openvz','openvz'), ('repy','repy')])
    name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all templates of the same tech. Cannot be changed. Not displayed.")
    diskspace = forms.IntegerField(label="Disk Space (MB)", required = False, help_text="only OpenVZ and KVMqm")
    cpus = forms.IntegerField(label="number of CPUs", required = False, help_text="Repy, OpenVZ: float number; KVMqm: integer number")
    def __init__(self, *args, **kwargs):
        super(AddProfileForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['tech', 'name', 'label', 'diskspace', 'cpus', 'ram', 'restricted', 'preference']

@wrap_rpc
def index(api, request):
    profile_list = api.resource_list('profile')
    return render_to_response("admin/device_profile/index.html", {'user': api.user, 'profile_list': profile_list, 'hostManager': is_hostManager(api.account_info())})


@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = AddProfileForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            
            data={'tech': formData['tech'],
                 'name': formData['name'],
                 'ram':formData['ram'],
                 'label':formData['label'],
                 'preference':formData['preference']}
            if formData['diskspace'] and (formData['tech'] != 'repy'):
                data['diskspace'] = formData['diskspace']
            if formData['cpus']:
                data['cpus'] = formData['cpus']
            if formData['restricted']:
                data['restricted'] = formData['restricted']
            
            api.resource_create('profile',data)
           
            return render_to_response("admin/device_profile/add_success.html", {'user': api.user, 'label': formData["label"],'tech':data['tech']})
        else:
            return render_to_response("admin/device_profile/form.html", {'user': api.user, 'form': form, "edit":False, 'tech':data['tech']})
    else:
        form = AddProfileForm
        return render_to_response("admin/device_profile/form.html", {'user': api.user, 'form': form, "edit":False, 'tech':data['tech']})

    
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
                return render_to_response("admin/device_profile/remove_success.html", {'user': api.user, 'label':label, 'tech':tech})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'invalid id','text':'There is no device profile with id '+res_id})
        else:
            res_id = request.POST['res_id']
            if res_id:
                form = RemoveResourceForm()
                form.fields["res_id"].initial = res_id
                return render_to_response("admin/device_profile/remove_confirm.html", {'user': api.user, 'label': api.resource_info(res_id)['attrs']['label'], 'tech': api.resource_info(res_id)['attrs']['tech'], 'hostManager': is_hostManager(api.account_info()), 'form': form})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    
    else:
        res_id = request.GET['id']
        if res_id:
            form = RemoveResourceForm()
            form.fields["res_id"].initial = res_id
            return render_to_response("admin/device_profile/remove_confirm.html", {'user': api.user, 'label': api.resource_info(res_id)['attrs']['label'], 'tech': api.resource_info(res_id)['attrs']['tech'], 'hostManager': is_hostManager(api.account_info()), 'form': form})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})
    
@wrap_rpc
def edit(api, request):
    if request.method=='POST':
        tech = request.POST['tech']
        if tech == 'repy':
            form = EditRePyForm(request.POST)
        else:
            if tech == 'openvz':
                form = EditOpenVZForm(request.POST)
            else:
                form = EditKVMqmForm(request.POST)
        
        if form.is_valid():
            formData = form.cleaned_data
            data={'cpus':formData['cpus'],
				 'ram':formData['ram'],
                 'label':formData['label'],
                 'preference':formData['preference']}
            if (formData['tech'] != 'repy'):
                data['diskspace'] = formData['diskspace']
            if formData['restricted']:
                data['restricted'] = formData['restricted']
            
            if api.resource_info(formData['res_id'])['type'] == 'profile':
                api.resource_modify(formData["res_id"],data)
                return render_to_response("admin/device_profile/edit_success.html", {'user': api.user, 'label': formData["label"],'tech':'repy'})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no repy device profile.'})
        else:
            label = request.POST["label"]
            if label:
                return render_to_response("admin/device_profile/form.html", {'user': api.user, 'label': label, 'tech':'repy', 'form': form, "edit":True})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        res_id = request.GET['id']
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            if origData['tech'] == 'repy':
                form = EditRePyForm(origData)
            else:
                if origData['tech'] == 'openvz':
                    form = EditOpenVZForm(origData)
                else:
                    form = EditKVMqmForm(origData)
            return render_to_response("admin/device_profile/form.html", {'user': api.user, 'label': res_info['attrs']['label'], 'tech':'repy', 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})
