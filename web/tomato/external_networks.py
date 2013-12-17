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
from admin_common import RemoveResourceForm

class NetworkForm(forms.Form):
    kind = forms.CharField(label="Kind",max_length=255)
    label = forms.CharField(max_length=255,label="Label",help_text="Visible Name")
    preference = forms.IntegerField(label="Preference", help_text="The item with the highest preference will be the default one. An integer number.")
    description = forms.CharField(widget = forms.Textarea, required=False)
    
   
class EditNetworkForm(NetworkForm):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    def __init__(self, *args, **kwargs):
        super(EditNetworkForm, self).__init__(*args, **kwargs)
        self.fields["kind"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["kind"].help_text=None
    
@wrap_rpc
def index(api, request):
    netw_list = api.resource_list('network')
    return render_to_response("admin/external_networks/index.html", {'user': api.user, 'netw_list': netw_list})

@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = NetworkForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            api.resource_create('network',{'kind':formData['kind'],
                                           'label':formData['label'],
                                           'preference':formData['preference'],
                                           'description':formData['description']})
           
            return render_to_response("admin/external_networks/add_success.html", {'user': api.user, 'label': formData["label"]})
        else:
            return render_to_response("admin/external_networks/form.html", {'user': api.user, 'form': form, "edit":False})
    else:
        form = NetworkForm
        return render_to_response("admin/external_networks/form.html", {'user': api.user, 'form': form, "edit":False,})


@wrap_rpc
def remove(api, request, res_id = None):
    if request.method == 'POST':
        form = RemoveResourceForm(request.POST)
        if form.is_valid():
            res_id = form.cleaned_data["res_id"]
            if api.resource_info(res_id) and api.resource_info(res_id)['type'] == 'network':
                label = api.resource_info(res_id)['attrs']['label']
                api.resource_remove(res_id)
                return render_to_response("admin/external_networks/remove_success.html", {'user': api.user, 'label':label})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'invalid id','text':'There is no external network with id '+res_id})
        else:
            if not res_id:
                res_id = request.POST['res_id']
            if res_id:
                form = RemoveResourceForm()
                form.fields["res_id"].initial = res_id
                return render_to_response("admin/external_networks/remove_confirm.html", {'user': api.user, 'label': api.resource_info(res_id)['attrs']['label'], 'form': form})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    
    else:
        if res_id:
            form = RemoveResourceForm()
            form.fields["res_id"].initial = res_id
            return render_to_response("admin/external_networks/remove_confirm.html", {'user': api.user, 'label': api.resource_info(res_id)['attrs']['label'], 'form': form})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})
    

@wrap_rpc
def edit(api, request, res_id = None):
    if request.method=='POST':
        form = EditNetworkForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if api.resource_info(formData['res_id'])['type'] == 'network':
                api.resource_modify(formData["res_id"],{'label':formData['label'],
                                                        'preference':formData['preference'],
                                                        'description':formData['description']})
                return render_to_response("admin/external_networks/edit_success.html", {'user': api.user, 'label': formData["label"], 'res_id': formData['res_id']})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no external network.'})
        else:
            kind = request.POST["kind"]
            if kind:
                return render_to_response("admin/external_networks/form.html", {'user': api.user, 'label': kind, 'form': form, "edit":True})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            form = EditNetworkForm(origData)
            return render_to_response("admin/external_networks/form.html", {'user': api.user, 'label': res_info['attrs']['label'], 'form': form, "edit":True})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})
