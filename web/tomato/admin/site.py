# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2014 Integrated Communication Systems Lab, University of Kaiserslautern
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




#TODO: fix add, edit and remove functions


'''
Created on Dec 4, 2014

@author: t-gerhard
'''

from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse

from tomato.crispy_forms.layout import Layout
from ..admin_common import Buttons
from ..lib import wrap_rpc
from . import add_function, edit_function, remove_function, AddEditForm, RemoveConfirmForm, append_empty_choice, organization_name_list, InputTransformerForm


geolocation_script = '<script>\n\
        function fillCoordinates() {\n\
            var address = document.getElementById("id_description").value;\n\
            queryAndFillCoordinates(address);\n\
        }\n\
        function queryAndFillCoordinates(address) {\n\
            var addr=encodeURIComponent(address);\n\
            $.ajax({\n\
                type: "GET",\n\
                async: true,\n\
                url: "//maps.googleapis.com/maps/api/geocode/json?sensor=false&address="+addr,\n\
                success: function(res) {\n\
                    var ret = res.results[0];\n\
                    if(ret) {\n\
                        loc = ret.geometry.location;\n\
                        document.getElementById("id_geolocation_latitude").value = loc.lat;\n\
                        document.getElementById("id_geolocation_longitude").value = loc.lng;\n\
                    } else {\n\
                        var address_new = prompt("Could not get the location for address. Enter a location to get the geolocation coordinates for");\n\
                        if (address_new != null) {\n\
                            queryAndFillCoordinates(address_new);\n\
                        }\n\
                    }\n\
                }\n\
              });\n\
            }\n\
        \n\
        var button = $("<button role=\\\"button\\\" onClick=\\\"fillCoordinates(); return false;\\\" class=\\\"btn btn-primary\\\"><span class=\\\"glyphicon glyphicon-globe\\\"> Fetch Geolocation</span></button>");\n\
        loc_field = $("#id_location")\n\
        loc_field.parent().append(button);\n\
    </script>'


class SiteForm(AddEditForm):
    name = forms.CharField(max_length=50, help_text="The name of the site. Must be unique to all sites. e.g.: ukl")
    description = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
    description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
    organization = forms.CharField(max_length=50)
    location = forms.CharField(max_length=255, help_text="e.g.: Germany")
    geolocation_longitude = forms.FloatField(help_text="Float Number. >0 if East, <0 if West",label="Geolocation: Longitude")
    geolocation_latitude = forms.FloatField(help_text="Float Number. >0 if North, <0 if South",label="Geolocation: Latitude")

    buttons = Buttons.cancel_add
    
    primary_key = "name"
    create_keys = ['name', 'organization', 'description']
    redirect_after = "tomato.admin.site.info"
    
    message_after = geolocation_script
    
    def __init__(self, orga_namelist, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.fields["organization"].widget = forms.widgets.Select(choices=orga_namelist)
        self.helper.layout = Layout(
	     'name',
	     'description',
	     'description_text',
	     'organization',
	     'location',
	     'geolocation_longitude',
	     'geolocation_latitude',
	     self.buttons
         )
        
    def get_values(self):
        formData = InputTransformerForm.get_values(self)
        formData['geolocation'] = {'longitude':formData['geolocation_longitude'],
                                   'latitude':formData['geolocation_latitude']}
        del formData['geolocation_longitude']
        del formData['geolocation_latitude']
                                              
        return formData
    
    def input_values(self, formData):
        if formData is not None and 'geolocation' in formData:
            formData['geolocation_longitude'] = formData['geolocation']['longitude']
            formData['geolocation_latitude'] = formData['geolocation']['latitude']
            del formData['geolocation']
        return formData
        
        
class AddSiteForm(SiteForm):
    title = "Add Site"
    formaction = "tomato.admin.site.add"
    formaction_haskeys = False
    def __init__(self, organization=None, *args, **kwargs):
        super(AddSiteForm, self).__init__(*args, **kwargs)
        if organization is not None:
            self.fields['organization'].initial = organization
        
    
class EditSiteForm(SiteForm):
    buttons = Buttons.cancel_save
    title = "Editing Site '%(name)s'"
    formaction = "tomato.admin.site.edit"
    def __init__(self, *args, **kwargs):
        super(EditSiteForm, self).__init__(*args, **kwargs)
        self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["name"].help_text=None
        
    
class RemoveSiteForm(RemoveConfirmForm):
    redirect_after_useargs = False
    formaction = "tomato.admin.site.remove"
    redirect_after = "tomato.admin.site.list"
    message="Are you sure you want to remove the site '%(name)s'?"
    title="Remove Site '%(name)s'"
    primary_key = 'name'
    
    
@wrap_rpc
def list(api, request):
    return HttpResponseRedirect(reverse("tomato.admin.organization.list"))

@wrap_rpc
def info(api, request, name):
    orga = api.site_info(name)['organization']
    return HttpResponseRedirect(reverse("tomato.admin.organization.info", kwargs={'name':orga}))    
    

@wrap_rpc
def add(api, request, organization=None):
    return add_function(request,
                        Form=AddSiteForm,
                        create_function=api.site_create,
                        clean_formkwargs= ({'organization':organization} if organization is not None else {}),
                        formkwargs = {'orga_namelist':append_empty_choice(organization_name_list(api))}
                        )

@wrap_rpc
def edit(api, request, name=None):
    return edit_function(request,
                         Form=EditSiteForm,
                         modify_function=api.site_modify,
                         primary_value=name,
                         clean_formargs=[api.site_info(name)],
                         formargs = [append_empty_choice(organization_name_list(api))]
                         )
    

    
@wrap_rpc
def remove(api, request, name):
    return remove_function(request,
                           Form=RemoveSiteForm,
                           delete_function=api.site_remove,
                           primary_value=name
                           )