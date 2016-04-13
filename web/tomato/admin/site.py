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




# TODO: fix add, edit and remove functions


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
from . import AddEditForm, RemoveConfirmForm, append_empty_choice, \
	organization_name_list

geolocation_script = '<script>\n\
        function fillCoordinates() {\n\
            var address = document.getElementById("id_label").value;\n\
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
	label = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
	description = forms.CharField(widget=forms.Textarea, label="Description", required=False)
	organization = forms.CharField(max_length=50)
	location = forms.CharField(max_length=255, help_text="e.g.: Germany")
	geolocation_longitude = forms.FloatField(help_text="Float Number. >0 if East, <0 if West",
											 label="Geolocation: Longitude")
	geolocation_latitude = forms.FloatField(help_text="Float Number. >0 if North, <0 if South",
											label="Geolocation: Latitude")

	buttons = Buttons.cancel_add

	message_after = geolocation_script

	def get_redirect_after(self):
		return HttpResponseRedirect(reverse("tomato.admin.site.info", kwargs={"name": self.cleaned_data['name']}))

	def __init__(self, orga_namelist, *args, **kwargs):
		super(SiteForm, self).__init__(*args, **kwargs)
		self.fields["organization"].widget = forms.widgets.Select(choices=orga_namelist)
		self.helper.layout = Layout(
			'name',
			'label',
			'description',
			'organization',
			'location',
			'geolocation_longitude',
			'geolocation_latitude',
			self.buttons
		)

class AddSiteForm(SiteForm):
	title = "Add Site"

	def __init__(self, organization=None, *args, **kwargs):
		super(AddSiteForm, self).__init__(*args, **kwargs)
		if organization is not None:
			self.fields['organization'].initial = organization

	def submit(self, api):
		formData = self.get_optimized_data()
		formData['geolocation'] = {'longitude': formData['geolocation_longitude'],
								   'latitude': formData['geolocation_latitude']}
		del formData['geolocation_longitude']
		del formData['geolocation_latitude']
		api.site_create(formData['name'], formData['organization'], formData['label'],
											{k: v for k, v in formData.iteritems() if k not in ('name', 'organization', 'label')})


class EditSiteForm(SiteForm):
	buttons = Buttons.cancel_save
	title = "Editing Site '%(name)s'"

	def __init__(self, data, *args, **kwargs):
		if data is not None and 'geolocation' in data and data['geolocation']:
			data['geolocation_longitude'] = data['geolocation']['longitude']
			data['geolocation_latitude'] = data['geolocation']['latitude']
			del data['geolocation']
		super(EditSiteForm, self).__init__(*args, data=data, **kwargs)
		self.fields["name"].widget = forms.TextInput(attrs={'readonly': 'readonly'})
		self.fields["name"].help_text = None

	def submit(self, api):
		formData = self.get_optimized_data()
		formData['geolocation'] = {'longitude': formData['geolocation_longitude'],
								   'latitude': formData['geolocation_latitude']}
		del formData['geolocation_longitude']
		del formData['geolocation_latitude']
		api.site_modify(formData['name'], {k: v for k, v in formData.iteritems() if k not in ('name',)})

class RemoveSiteForm(RemoveConfirmForm):
	message = "Are you sure you want to remove the site '%(name)s'?"
	title = "Remove Site '%(name)s'"


@wrap_rpc
def list(api, request):
	return HttpResponseRedirect(reverse("tomato.admin.organization.list"))


@wrap_rpc
def info(api, request, name):
	orga = api.site_info(name)['organization']
	return HttpResponseRedirect(reverse("tomato.admin.organization.info", kwargs={'name': orga}))


@wrap_rpc
def add(api, request, organization=None):
	if request.method == 'POST':
		form = AddSiteForm(data=request.POST,
												orga_namelist=append_empty_choice(organization_name_list(api)))
		if form.is_valid():
			form.submit(api)
			return form.get_redirect_after()
		else:
			return form.create_response(request)
	else:
		form = AddSiteForm(organization=organization,
												orga_namelist=append_empty_choice(organization_name_list(api)))
		return form.create_response(request)


@wrap_rpc
def edit(api, request, name=None):
	if request.method == 'POST':
		form = EditSiteForm(orga_namelist=append_empty_choice(organization_name_list(api)),
													data=request.POST)
		if form.is_valid():
			form.submit(api)
			return form.get_redirect_after()
		else:
			return form.create_response(request)
	else:
		form = EditSiteForm(orga_namelist=append_empty_choice(organization_name_list(api)),
													data=api.site_info(name))
		return form.create_response(request)

@wrap_rpc
def remove(api, request, name):
	if request.method == 'POST':
		form = RemoveSiteForm(name=name, data=request.POST)
		if form.is_valid():
			organization_name = api.site_info(name)['organization']
			api.site_remove(name)
			return HttpResponseRedirect(reverse('tomato.admin.organization.info', kwargs={'name': organization_name}))
	form = RemoveSiteForm(name=name)
	return form.create_response(request)

