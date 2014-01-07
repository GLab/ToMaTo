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

from django.shortcuts import render
from django import forms
from lib import wrap_rpc

class OrganizationForm(forms.Form):
    name = forms.CharField(max_length=50, help_text="The name of the organization. Must be unique to all organizations. e.g.: ukl")
    description = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
    homepage_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org")
    image_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org/logo.png")
    description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
    
class EditOrganizationForm(OrganizationForm):
    def __init__(self, *args, **kwargs):
        super(EditOrganizationForm, self).__init__(*args, **kwargs)
        self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["name"].help_text=None
    
class RemoveOrganizationForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.HiddenInput)

@wrap_rpc
def index(api, request):
    return render(request, "admin/organization/index.html", {'organization_list': api.organization_list()})

@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.organization_create(formData["name"],formData["description"])
            api.organization_modify(formData["name"],{"homepage_url": formData["homepage_url"],
                                              'image_url':formData['image_url'],
                                              'description_text':formData['description_text']
                                              })
            return render(request, "admin/organization/add_success.html", {'name': formData["name"]})
        else:
            return render(request, "admin/organization/form.html", {'form': form, "edit":False})
    else:
        form = OrganizationForm
        return render(request, "admin/organization/form.html", {'form': form, "edit":False})
    
@wrap_rpc
def remove(api, request, name=None):
    if request.method == 'POST':
        form = RemoveOrganizationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            api.organization_remove(name)
            return render(request, "admin/organization/remove_success.html", {'name': name})
        else:
            if not name:
                name = request.POST['name']
            if name:
                form = RemoveOrganizationForm()
                form.fields["name"].initial = name
                return render(request, "admin/organization/remove_confirm.html", {'name': name, 'form': form})
            else:
                return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    
    else:
        if name:
            form = RemoveOrganizationForm()
            form.fields["name"].initial = name
            return render(request, "admin/organization/remove_confirm.html", {'name': name, 'form': form})
        else:
            return render(request, "main/error.html",{'type':'not enough parameters','text':'No organization specified. Have you followed a valid link?'})
    
@wrap_rpc
def edit(api, request, name=None):
    if request.method=='POST':
        form = EditOrganizationForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.organization_modify(formData["name"],{"description": formData["description"],
                                                      "homepage_url": formData["homepage_url"],
                                                      'image_url':formData['image_url'],
                                                      'description_text':formData['description_text']
                                                      })
            return render(request, "admin/organization/edit_success.html", {'name': formData["name"]})
        else:
            if not name:
                name=request.POST["name"]
            if name:
                form.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
                form.fields["name"].help_text=None
                return render(request, "admin/organization/form.html", {'name': name, 'form': form, "edit":True})
            else:
                return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
            
    else:
        if name:
            orgaInfo = api.organization_info(name)
            form = EditOrganizationForm(orgaInfo)
            return render(request, "admin/organization/form.html", {'name': name, 'form': form, "edit":True})
        else:
            return render(request, "main/error.html",{'type':'not enough parameters','text':'No organization specified. Have you followed a valid link?'})
