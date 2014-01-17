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
from django.http import HttpResponseRedirect

from admin_common import BootstrapForm, RemoveConfirmForm
from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import FormActions, StrictButton
from django.core.urlresolvers import reverse

class HostForm(BootstrapForm):
	address = forms.CharField(max_length=255,help_text="The host's IP address. This is also its unique id.")
	site = forms.CharField(max_length=50,help_text="The site this host belongs to.")
	enabled = forms.BooleanField(initial=True, required=False,help_text="Whether this host is enabled.")
	description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
	okbutton_text = '<span class="glyphicon glyphicon-accept"></span> Add'
	def __init__(self, api, *args, **kwargs):
		super(HostForm, self).__init__(*args, **kwargs)
		self.fields["site"].widget = forms.widgets.Select(choices=site_name_list(api))
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
			'address',
			'site',
			'enabled',
			'description_text',
			FormActions(
				StrictButton('<span class="glyphicon glyphicon-remove"></span> Cancel', css_class='btn-danger backbutton'),
				StrictButton(self.okbutton_text, css_class='btn-success', type="submit")
			)
		)
	
class EditHostForm(HostForm):
	okbutton_text = '<span class="glyphicon glyphicon-accept"></span> Save'
	def __init__(self, api, address, *args, **kwargs):
		super(EditHostForm, self).__init__(api, *args, **kwargs)
		self.fields["address"].widget=forms.TextInput(attrs={'readonly':'readonly'})
		self.fields["address"].help_text=None
		self.helper.form_action = reverse(edit, kwargs={"address": address})
		
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
	site_map = dict([(s["name"], "%s, %s" % (s["description"] if s["description"] else s["name"], s["location"])) for s in api.site_list()])
	return render(request, "host/list.html", {'host_list': hosts, 'organizations': organizations, 'site_map': site_map, 'sites': sites, 'site': site, 'organization': organization})

@wrap_rpc
def info(api, request, address):
	host = api.host_info(address)
	site = api.site_info(host["site"])
	organization = api.organization_info(host["organization"])
	return render(request, "host/info.html", {'host': host, 'organization': organization, 'site': site})

@wrap_rpc
def add(api, request):
	message_after = '<h2>Public key</h2>	The public key of this backend is:	<pre><tt>'+api.server_info()['public_key']+'</tt></pre>'
	if request.method == 'POST':
		form = HostForm(api, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.host_create(formData["address"],formData["site"], {"enabled": formData["enabled"],'description_text':formData['description_text']})
			return HttpResponseRedirect(reverse("host.info", kwargs={"address": formData["address"]}))
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Host", 'message_after':message_after})
	else:
		form = HostForm(api)
		if api.site_list():
			return render(request, "form.html", {'form': form, "heading":"Add Host", 'message_after':message_after})
		else:
			return render(request, "main/error.html",{'type':'No site available','text':'You need a site first before you can add hosts.'})

@wrap_rpc
def remove(api, request, address=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.host_remove(address)
			return HttpResponseRedirect(reverse("host_list"))
	form = RemoveConfirmForm.build(reverse("tomato.host.remove", kwargs={"address": address}))
	return render(request, "form.html", {"heading": "Remove Host", "message_before": "Are you sure you want to remove the host '"+address+"'?", 'form': form})

@wrap_rpc
def edit(api, request, address=None):
	if request.method=='POST':
		form = EditHostForm(api, address, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.host_modify(formData["address"],{'site':formData["site"], "enabled": formData["enabled"],'description_text':formData['description_text']})
			return HttpResponseRedirect(reverse("host.info", kwargs={"address": address}))
		else:
			if not address:
				address=request.POST["address"]
			if address:
				return render(request, "form.html", {"heading": "Editing Host '"+address+"'", 'form': form})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	else:
		if address:
			hostinfo=api.host_info(address)
			form = EditHostForm(api, address, hostinfo)
			form.fields["site"].initial = hostinfo["site"]
			form.fields["enabled"].initial = hostinfo["enabled"]
			return render(request, "form.html", {"heading": "Editing Host '"+address+"'", 'form': form})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})
