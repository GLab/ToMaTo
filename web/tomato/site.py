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

from django import forms
from lib import *
from admin_common import is_hostManager, organization_name_list

class SiteForm(forms.Form):
    name = forms.CharField(max_length=50, help_text="The name of the site. Must be unique to all sites. e.g.: ukl")
    description = forms.CharField(max_length=255, help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
    organization = forms.CharField(max_length=50)
    location = forms.CharField(max_length=255, help_text="e.g.: Germany")
    geolocation_longitude = forms.FloatField(help_text="Float Number. >0 if East, <0 if West",label="Geolocation: Longitude")
    geolocation_latitude = forms.FloatField(help_text="Float Number. >0 if North, <0 if South",label="Geolocation: Latitude")
    def __init__(self, api, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.fields["organization"].widget = forms.widgets.Select(choices=organization_name_list(api))
    
class EditSiteForm(SiteForm):
    def __init__(self, api, *args, **kwargs):
        super(EditSiteForm, self).__init__(api, *args, **kwargs)
        self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["name"].help_text=None
    
class RemoveSiteForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.HiddenInput)
    


@wrap_rpc
def index(api, request):
    return render_to_response("admin/site/index.html", {'user': api.user, 'site_list': api.site_list(), 'hostManager': is_hostManager(api.account_info())})

@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = SiteForm(api, request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.site_create(formData["name"],formData['organization'],formData["description"])
            api.site_modify(formData["name"],{"location": formData["location"],
                                              'geolocation':{'longitude':formData['geolocation_longitude'],
                                                             'latitude':formData['geolocation_latitude']},
                                              'organization':formData['organization']})
            return render_to_response("admin/site/add_success.html", {'user': api.user, 'name': formData["name"]})
        else:
            return render_to_response("admin/site/form.html", {'user': api.user, 'form': form, "edit":False})
    else:
        form = SiteForm(api)
        return render_to_response("admin/site/form.html", {'user': api.user, 'form': form, "edit":False})
    
@wrap_rpc
def remove(api, request, name=None):
    if request.method == 'POST':
        form = RemoveSiteForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            api.site_remove(name)
            return render_to_response("admin/site/remove_success.html", {'user': api.user, 'name': name})
        else:
            if not name:
                name = request.POST['name']
            if name:
                form = RemoveSiteForm()
                form.fields["name"].initial = name
                return render_to_response("admin/site/remove_confirm.html", {'user': api.user, 'name': name, 'hostManager': is_hostManager(api.account_info()), 'form': form})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    
    else:
        if name:
            form = RemoveSiteForm()
            form.fields["name"].initial = name
            return render_to_response("admin/site/remove_confirm.html", {'user': api.user, 'name': name, 'hostManager': is_hostManager(api.account_info()), 'form': form})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No site specified. Have you followed a valid link?'})
    
@wrap_rpc
def edit(api, request, name=None):
    if request.method=='POST':
        form = EditSiteForm(api, request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.site_modify(formData["name"],{'description':formData["description"],
                                              'location':formData["location"],
                                              'geolocation':{'longitude':formData['geolocation_longitude'],
                                                             'latitude':formData['geolocation_latitude']},
                                              'organization':formData['organization']})
            return render_to_response("admin/site/edit_success.html", {'user': api.user, 'name': formData["name"]})
        else:
            if not name:
                name=request.POST["name"]
            if name:
                form.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
                form.fields["name"].help_text=None
                return render_to_response("admin/site/form.html", {'user': api.user, 'name': name, 'form': form, "edit":True})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
            
    else:
        if name:
            siteInfo = api.site_info(name)
            siteInfo['geolocation_longitude'] = siteInfo['geolocation'].get('longitude',0)
            siteInfo['geolocation_latitude'] = siteInfo['geolocation'].get('latitude',0)
            del siteInfo['geolocation']
            form = EditSiteForm(api, siteInfo)
            return render_to_response("admin/site/form.html", {'user': api.user, 'name': name, 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No site specified. Have you followed a valid link?'})
