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

class TemplateForm(forms.Form):
    name = forms.CharField(max_length=50,label="Internal Name")
    label = forms.CharField(max_length=255)
    subtype = forms.CharField(max_length=255)
    tech = forms.CharField(max_length=255,widget = forms.widgets.Select(choices={('kvmqm','kvmqm'),('openvz','openvz'),('repy','repy')}))
    preference = forms.IntegerField(label="Preference")

class AddTemplateForm(TemplateForm):
    torrentfile  = forms.FileField(label="Torrent:")
    
class EditTemplateForm(TemplateForm):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
class ChangeTemplateTorrentForm(forms.Form):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    torrentfile  = forms.FileField(label="Torrent containing image:")    
    
class RemoveTemplateForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
def is_hostManager(account_info):
	return 'hosts_manager' in account_info['flags']

@wrap_rpc
def index(api, request):
    reslist = api.resource_list()
    templ_list = []
    for res in reslist:
        if res['type'] == 'template':
            templ_list.append(res)
        
    return render_to_response("admin/vhosttemplates/index.html", {'templ_list': templ_list, 'hostManager': is_hostManager(api.account_info())})


@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = AddTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            formData = form.cleaned_data
            f = request.FILES['file']
            #
            #
            #   DUMMY
            #
            #
            return render_to_response("admin/vhosttemplates/add_success.html", {'label': formData['label']})
        else:
            return render_to_response("admin/vhosttemplates/form.html", {'form': form, "edit":False})
    else:
        form = AddTemplateForm
        return render_to_response("admin/vhosttemplates/form.html", {'form': form, "edit":False})
   

@wrap_rpc
def remove(api, request):
    return index(api,request)
    #
    #
    #   DUMMY
    #
    #

@wrap_rpc
def edit(api, request):
    return render_to_response("admin/vhosttemplates/edit_unspecified.html",{'res_id':request.GET['id'],'label':api.resource_info(request.GET['id'])['attrs']['label']})

@wrap_rpc
def edit_data(api, request):
    if request.method=='POST':
        form = EditTemplateForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if api.resource_info(formData['res_id'])['type'] == 'template':
                api.resource_modify(formData["res_id"],{'name':formData['name'],'label':formData['label'],'subtype':formData['subtype'],'preference':formData['preference']})
                return render_to_response("admin/vhosttemplates/edit_success.html", {'label': formData["label"]})
            else:
                return render_to_response("main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no template.'})
        else:
            name="ERROR"
            return render_to_response("admin/vhosttemplates/form.html", {'label': name, 'form': form, "edit":True, 'edit_data':True})
    else:
        res_id = request.GET['id']
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            form = EditTemplateForm(origData)
            return render_to_response("admin/vhosttemplates/form.html", {'label': res_info['attrs']['label'], 'form': form, "edit":True, 'edit_data':True})
        else:
            return render_to_response("main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})


@wrap_rpc
def edit_torrent(api, request):
    return index(api,request)
    #
    #
    #   DUMMY
    #
    #

