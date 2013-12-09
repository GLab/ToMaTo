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


from django import forms
from lib import *

class HostForm(forms.Form):
    address = forms.CharField(max_length=255,help_text="The host's IP address. This is also its unique id.")
    site = forms.CharField(max_length=50,help_text="The site this host belongs to.")
    enabled = forms.BooleanField(initial=True, required=False,help_text="Whether this host is enabled.")
    def __init__(self, api, *args, **kwargs):
        super(HostForm, self).__init__(*args, **kwargs)
        self.fields["site"].widget = forms.widgets.Select(choices=site_name_list(api))
    
class EditHostForm(HostForm):
    def __init__(self, api, *args, **kwargs):
        super(EditHostForm, self).__init__(api, *args, **kwargs)
        self.fields["address"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["address"].help_text=None
    
class RemoveHostForm(forms.Form):
    address = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
    
def site_name_list(api):
    l = api.site_list()
    res = []
    for site in l:
        res.append((site["name"],site["description"] or site["name"]))
    res.sort()
    return res

@wrap_rpc
def index(api, request):
        sites = dict([(s["name"], "%s, %s" % (s["description"] if s["description"] else s["name"], s["location"])) for s in api.site_list()])
        return render_to_response("admin/host/index.html", {'user': api.user, 'host_list': api.host_list(), 'sites': sites})

@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = HostForm(api, request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.host_create(formData["address"],formData["site"], {"enabled": formData["enabled"]})
            return render_to_response("admin/host/add_success.html", {'user': api.user, 'address': formData["address"]})
        else:
            return render_to_response("admin/host/form.html", {'user': api.user, 'form': form, "edit":False})
    else:
        form = HostForm(api)
        if api.site_list():
            return render_to_response("admin/host/form.html", {'user': api.user, 'public_key': api.host_public_key(), 'form': form, "edit":False})
        else:
            return render_to_response("admin/host/error_no_site.html", {'user': api.user})
   
@wrap_rpc
def remove(api, request, address=None):
    if request.method == 'POST':
        form = RemoveHostForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data["address"]
            api.host_remove(address)
            return render_to_response("admin/host/remove_success.html", {'user': api.user, 'address': address})
        else:
            if not address:
                address=request.POST['address']
            if address:
                form.fields["address"].initial = address
                return render_to_response("admin/host/remove_confirm.html", {'user': api.user, 'address': address, 'form': form})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        if address:
            form = RemoveHostForm()
            form.fields["address"].initial = address
            return render_to_response("admin/host/remove_confirm.html", {'user': api.user, 'address': address, 'form': form})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})

@wrap_rpc
def edit(api, request, address=None):
    if request.method=='POST':
        form = EditHostForm(api, request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.host_modify(formData["address"],{'site':formData["site"], "enabled": formData["enabled"]})
            return render_to_response("admin/host/edit_success.html", {'user': api.user, 'address': formData["address"]})
        else:
            if not address:
                address=request.POST["address"]
            if address:
                return render_to_response("admin/host/form.html", {'user': api.user, 'address': address, 'form': form, "edit":True})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        if address:
            hostinfo=api.host_info(address)
            form = EditHostForm(api, hostinfo)
            form.fields["site"].initial = hostinfo["site"]
            form.fields["enabled"].initial = hostinfo["enabled"]
            return render_to_response("admin/host/form.html", {'user': api.user, 'address': address, 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})
