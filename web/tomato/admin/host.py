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

from django.shortcuts import render
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from tomato.crispy_forms.layout import Layout
from ..admin_common import Buttons
from ..lib import wrap_rpc
from . import AddEditForm, RemoveConfirmForm, append_empty_choice, \
	site_name_list


class HostForm(AddEditForm):
	name = forms.CharField(max_length=255, help_text="The host's name. This is also its unique id.")
	address = forms.CharField(max_length=255, help_text="The host's IP address.")
	rpcurl = forms.CharField(max_length=255, help_text="The host's RPC url.")
	site = forms.CharField(max_length=50, help_text="The site this host belongs to.")
	enabled = forms.BooleanField(initial=True, required=False, help_text="Whether this host is enabled.")
	description = forms.CharField(widget=forms.Textarea, label="Description", required=False)

	buttons = Buttons.cancel_add

	def __init__(self, site_namelist, *args, **kwargs):
		super(HostForm, self).__init__(*args, **kwargs)
		self.fields["site"].widget = forms.widgets.Select(choices=site_namelist)
		self.helper.layout = Layout(
			'name',
			'address',
			'rpcurl',
			'site',
			'enabled',
			'description',
			self.buttons
		)

	def get_redirect_after(self):
		return HttpResponseRedirect(reverse("tomato.admin.host.info", kwargs={"name": self.cleaned_data['name']}))

class AddHostForm(HostForm):
	title = "Add Host"

	def __init__(self, site=None, publickey=None, *args, **kwargs):
		super(AddHostForm, self).__init__(*args, **kwargs)
		if publickey is not None:
			self.message_after = \
				'<div class="row">\
					<div class="panel-group col-sm-10 col-sm-offset-2 col-lg-8 col-lg-offset-2">\
						<div class="panel panel-default">\
							<div class="panel-heading">\
								<h4 class="panel-title">\
									<a data-toggle="collapse" data-parent="#accordion" href="#collapseOne">\
										<span class="glyphicon glyphicon-lock"></span> Backend Public Key <small>(click to expand)</small>\
									</a>\
								</h4>\
							</div>\
							<div id="collapseOne" class="panel-collapse collapse" style="padding:0.2cm;">\
								<pre style="border: none; background: transparent;">%s</pre>\
							</div>\
						</div>\
					</div>\
				</div>' % publickey
		if site is not None:
			self.fields['site'].initial = site

	def submit(self, api):
		formData = self.cleaned_data
		api.host_create(formData['name'], formData['site'],
											{k: v for k, v in formData.iteritems() if k not in ('name', 'site')})




class EditHostForm(HostForm):
	buttons = Buttons.cancel_save
	title = "Editing Host '%(name)s'"

	def __init__(self, *args, **kwargs):
		super(EditHostForm, self).__init__(*args, **kwargs)
		self.fields["name"].widget = forms.TextInput(attrs={'readonly': 'readonly'})
		self.fields["name"].help_text = None

	def submit(self, api):
		formData = self.cleaned_data
		api.host_modify(formData['name'], {k: v for k, v in formData.iteritems() if k not in ('name',)})

class RemoveHostForm(RemoveConfirmForm):
	message = "Are you sure you want to remove the host '%(name)s'?"
	title = "Remove Host '%(name)s'"


@wrap_rpc
def list(api, request, site=None, organization=None):
	organizations = api.organization_list()
	sites = api.site_list()
	hosts = api.host_list(site=site, organization=organization)
	site_label = None
	organization_label = None
	if site:
		site_label = api.site_info(site)['label']
	if organization:
		organization_label = api.organization_info(organization)['label']
	site_map = dict(
		[(s["name"], "%s, %s" % (s["label"] if s["label"] else s["name"], s["location"])) for s in api.site_list()])
	return render(request, "host/list.html",
		{'host_list': hosts, 'organizations': organizations, 'site_map': site_map, 'sites': sites, 'site': site,
		'site_label': site_label, 'organization': organization, 'organization_label': organization_label})


@wrap_rpc
def info(api, request, name):
	host = api.host_info(name)
	host['element_types'].sort()
	host['connection_types'].sort()
	site = api.site_info(host["site"])
	organization = api.organization_info(host["organization"])
	return render(request, "host/info.html", {'host': host, 'organization': organization, 'site': site})


@wrap_rpc
def add(api, request, site=None):
	if request.method == 'POST':
		form = AddHostForm(data=request.POST,
												site_namelist=append_empty_choice(site_name_list(api)),
												publickey=api.server_info().get("public_key", "unknown"))
		if form.is_valid():
			form.submit(api)
			return form.get_redirect_after()
		else:
			return form.create_response(request)
	else:
		form = AddHostForm(site=site,
												site_namelist=append_empty_choice(site_name_list(api)),
												publickey=api.server_info().get("public_key", "unknown"))
		return form.create_response(request)


@wrap_rpc
def edit(api, request, name=None):
	if request.method == 'POST':
		form = EditHostForm(site_namelist=append_empty_choice(site_name_list(api)),
												data=request.POST)
		if form.is_valid():
			form.submit(api)
			return form.get_redirect_after()
		else:
			return form.create_response(request)
	else:
		form = EditHostForm(site_namelist=append_empty_choice(site_name_list(api)),
												data=api.host_info(name))
		return form.create_response(request)

@wrap_rpc
def remove(api, request, name):
	if request.method == 'POST':
		form = RemoveHostForm(name=name, data=request.POST)
		if form.is_valid():
			api.host_remove(name)
			return HttpResponseRedirect(reverse('tomato.admin.host.list'))
	form = RemoveHostForm(name=name)
	return form.create_response(request)
