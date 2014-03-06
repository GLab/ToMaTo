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
from lib import wrap_rpc, serverInfo
from django.http import HttpResponseRedirect

from admin_common import BootstrapForm, RemoveConfirmForm, Buttons
from tomato.crispy_forms.layout import Layout
from django.core.urlresolvers import reverse

class HostForm(BootstrapForm):
	name = forms.CharField(max_length=255,help_text="The host's name. This is also its unique id.")
	address = forms.CharField(max_length=255,help_text="The host's IP address.")
	site = forms.CharField(max_length=50,help_text="The site this host belongs to.")
	enabled = forms.BooleanField(initial=True, required=False,help_text="Whether this host is enabled.")
	description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
	buttons = Buttons.cancel_add
	def __init__(self, api, *args, **kwargs):
		super(HostForm, self).__init__(*args, **kwargs)
		self.fields["site"].widget = forms.widgets.Select(choices=site_name_list(api))
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
			'name',
			'address',
			'site',
			'enabled',
			'description_text',
			self.buttons
		)
	
class EditHostForm(HostForm):
	buttons = Buttons.cancel_save
	def __init__(self, api, name, *args, **kwargs):
		super(EditHostForm, self).__init__(api, *args, **kwargs)
		self.helper.form_action = reverse(edit, kwargs={"name": name})
		
def site_name_list(api):
	l = api.site_list()
	res = []
	for site in l:
		res.append((site["name"],site["description"] or site["name"]))
	res.sort()
	return res

@wrap_rpc
def list(api, request, site=None, organization=None):	
	organizations = api.organization_list()
	sites = api.site_list()
	hosts = api.host_list(site=site, organization=organization)
	site_description=None
	organization_description=None
	if site:
		site_description=api.site_info(site)['description']
	if organization:
		organization_description = api.organization_info(organization)['description']
	site_map = dict([(s["name"], "%s, %s" % (s["description"] if s["description"] else s["name"], s["location"])) for s in api.site_list()])
	return render(request, "host/list.html", {'host_list': hosts, 'organizations': organizations, 'site_map': site_map, 'sites': sites, 'site': site, 'site_description':site_description, 'organization': organization, 'organization_description': organization_description})

@wrap_rpc
def info(api, request, name):
	host = api.host_info(name)
	site = api.site_info(host["site"])
	organization = api.organization_info(host["organization"])
	return render(request, "host/info.html", {'host': host, 'organization': organization, 'site': site})

@wrap_rpc
def add(api, request):
	message_after = '<h2>Public key</h2>	The public key of this backend is:	<pre><tt>'+serverInfo()['public_key']+'</tt></pre>'
	if request.method == 'POST':
		form = HostForm(api, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.host_create(formData["name"], formData["site"], {"address": formData["address"], "enabled": formData["enabled"],'description_text':formData['description_text']})
			return HttpResponseRedirect(reverse("tomato.host.info", kwargs={"name": formData["name"]}))
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Host", 'message_after':message_after})
	else:
		form = HostForm(api)
		if api.site_list():
			return render(request, "form.html", {'form': form, "heading":"Add Host", 'message_after':message_after})
		else:
			return render(request, "main/error.html",{'type':'No site available','text':'You need a site first before you can add hosts.'})

@wrap_rpc
def remove(api, request, name=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.host_remove(name)
			return HttpResponseRedirect(reverse("host_list"))
	form = RemoveConfirmForm.build(reverse("tomato.host.remove", kwargs={"name": name}))
	return render(request, "form.html", {"heading": "Remove Host", "message_before": "Are you sure you want to remove the host '"+name+"'?", 'form': form})

@wrap_rpc
def edit(api, request, name=None):
	if request.method=='POST':
		form = EditHostForm(api, name, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.host_modify(name,{"name": formData["name"], "address": formData["address"], 'site':formData["site"], "enabled": formData["enabled"],'description_text':formData['description_text']})
			return HttpResponseRedirect(reverse("tomato.host.info", kwargs={"name": formData["name"]}))
		else:
			if not name:
				name=request.POST["name"]
			if name:
				return render(request, "form.html", {"heading": "Editing Host '"+name+"'", 'form': form})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	else:
		if name:
			hostinfo=api.host_info(name)
			form = EditHostForm(api, name, hostinfo)
			form.fields["site"].initial = hostinfo["site"]
			form.fields["enabled"].initial = hostinfo["enabled"]
			return render(request, "form.html", {"heading": "Editing Host '"+name+"'", 'form': form})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})
