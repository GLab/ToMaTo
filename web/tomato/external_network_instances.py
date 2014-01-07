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

from django.shortcuts import render
from django import forms
from lib import wrap_rpc
from admin_common import RemoveResourceForm

class NetworkInstanceForm(forms.Form):
    host = forms.CharField(label="Host")
    bridge = forms.CharField(max_length=255,label="Bridge",help_text="TODO: write a useful help text here...")
    network = forms.CharField(label="Network")
    def __init__(self, api, *args, **kwargs):
        super(NetworkInstanceForm, self).__init__(*args, **kwargs)
        self.fields["network"].widget = forms.widgets.Select(choices=external_network_list(api))
        self.fields["host"].widget = forms.widgets.Select(choices=host_list(api))
    
class EditNetworkInstanceForm(NetworkInstanceForm):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    def __init__(self, api, *args, **kwargs):
        super(EditNetworkInstanceForm, self).__init__(api, *args, **kwargs)
    
    
def external_network_list(api):
    l = api.resource_list('network')
    res = []
    for netw in l:
        res.append((netw["attrs"]["kind"],netw["attrs"]["label"] + ' -- ' + netw["attrs"]["kind"] ))
    res.sort()
    return res

def host_list(api):
    l = api.host_list()
    res = []
    for host in l:
        res.append((host['address'],host['address']))
    res.sort()
    return res


@wrap_rpc
def index(api, request):
    netwI_list = api.resource_list('network_instance')
    return render(request, "admin/external_network_instances/index.html", {'netwI_list': netwI_list})

@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = NetworkInstanceForm(api, request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('network_instance',{'host':formData['host'],
                                           'bridge':formData['bridge'],
                                           'network':formData['network'],
                                           'kind':formData['network']})
           
            return render(request, "admin/external_network_instances/add_success.html", {'label': formData["host"]})
        else:
            return render(request, "admin/external_network_instances/form.html", {'form': form, "edit":False})
    else:
        form = NetworkInstanceForm(api)
        return render(request, "admin/external_network_instances/form.html", {'form': form, "edit":False,})
    
   
@wrap_rpc
def remove(api, request, res_id = None):
    if request.method == 'POST':
        form = RemoveResourceForm(request.POST)
        if form.is_valid():
            res_id = form.cleaned_data["res_id"]
            if api.resource_info(res_id) and api.resource_info(res_id)['type'] == 'network_instance':
                label = api.resource_info(res_id)['attrs']['host']
                api.resource_remove(res_id)
                return render(request, "admin/external_network_instances/remove_success.html", {'label': label})
            else:
                return render(request, "main/error.html",{'type':'invalid id','text':'There is no external network instance with id '+res_id})
        else:
            if not res_id:
                res_id = request.POST['res_id']
            if res_id:
                form = RemoveResourceForm()
                form.fields["res_id"].initial = res_id
                return render(request, "admin/external_network_instances/remove_confirm.html", {'label': api.resource_info(res_id)['attrs']['host'], 'form': form})
            else:
                return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    
    else:
        if res_id:
            form = RemoveResourceForm()
            form.fields["res_id"].initial = res_id
            return render(request, "admin/external_network_instances/remove_confirm.html", {'label': api.resource_info(res_id)['attrs']['host'], 'form': form})
        else:
            return render(request, "main/error.html",{'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})
    

@wrap_rpc
def edit(api, request, res_id = None):
    if request.method=='POST':
        form = EditNetworkInstanceForm(api, request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if api.resource_info(formData['res_id'])['type'] == 'network_instance':
                api.resource_modify(formData["res_id"],{'host':formData['host'],
                                                        'bridge':formData['bridge'],
                                                        'network':formData['network'],
                                                        'kind':formData['network']}) 
                return render(request, "admin/external_network_instances/edit_success.html", {'label': formData["host"], 'res_id': formData['res_id']})
            else:
                return render(request, "main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no external network instance.'})
        else:
            host = request.POST["host"]
            if host:
                return render(request, "admin/external_network_instances/form.html", {'label': host, 'form': form, "edit":True})
            else:
                return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            form = EditNetworkInstanceForm(api, origData)
            return render(request, "admin/external_network_instances/form.html", {'label': res_info['attrs']['host'], 'form': form, "edit":True})
        else:
            return render(request, "main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})
