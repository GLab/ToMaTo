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

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from lib import wrap_rpc
from admin_common import RemoveConfirmForm, BootstrapForm, Buttons, append_empty_choice

from tomato.crispy_forms.layout import Layout

from django.core.urlresolvers import reverse

class NetworkInstanceForm(BootstrapForm):
	host = forms.CharField(label="Host")
	bridge = forms.CharField(max_length=255,label="Bridge",help_text="TODO: write a useful help text here...")
	network = forms.CharField(label="Network")
	def __init__(self, api, *args, **kwargs):
		super(NetworkInstanceForm, self).__init__(*args, **kwargs)
		self.fields["network"].widget = forms.widgets.Select(choices=append_empty_choice(external_network_list(api)))
		self.fields["host"].widget = forms.widgets.Select(choices=append_empty_choice(host_list(api)))
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
			'host',
			'bridge',
			'network',
			Buttons.cancel_add
		)
	
class EditNetworkInstanceForm(NetworkInstanceForm):
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	def __init__(self, res_id, api, *args, **kwargs):
		super(EditNetworkInstanceForm, self).__init__(api, *args, **kwargs)
		self.helper.form_action = reverse(edit, kwargs={"res_id": res_id})
		self.helper.layout = Layout(
			'res_id',
			'host',
			'bridge',
			'network',
			Buttons.cancel_save
		)
	
	
def external_network_list(api):
	l = api.resource_list('network')
	res = []
	for netw in l:
		res.append((netw["attrs"]["kind"],netw["attrs"]["label"] + ' -- ' + netw["attrs"]["kind"] ))
	res.sort()
	return res

def host_list(api):
	l = api.host_list()
	res = []
	for host in l:
		res.append((host['name'],host['name']))
	res.sort()
	return res

def network_id(api, kind, networks=None):
	if not networks:
		networks = api.resource_list("network")
	for net in networks:
		if net["attrs"]["kind"] == kind:
			return net["id"]

@wrap_rpc
def list(api, request, network=None, host=None, organization=None, site=None):
	nis = api.resource_list('network_instance')
	networks = api.resource_list('network')
	hosts = api.host_list()
	sites = api.site_list()
	organizations = api.organization_list()
	network_kind = None
	network_label = None
	organization_description=None
	site_description=None
	if site:
		site_description=api.site_info(site)['description']
	if organization:
		organization_description = api.organization_info(organization)['description']
	if network:
		network = int(network)
		for net in networks:
			if net["id"] == network:
				network_kind = net["attrs"]["kind"]
				network_label = net["attrs"]["label"]
	nis = filter(lambda ni: (not network or ni["attrs"]["network"] == network_kind) and (not host or ni["attrs"]["host"] == host), nis)
	
	if organization or site:
		nis_new=[]
		host_dict ={}
		for h in hosts:
			host_dict[h['name']] = h
		for ni in nis:
			if (not organization or host_dict[ni['attrs']['host']]['organization'] == organization) and (not site or host_dict[ni['attrs']['host']]['site'] == site):
				nis_new.append(ni)
		nis = nis_new
	
	return render(request, "external_network_instances/list.html", {'nis': nis, "networks": networks, "hosts": hosts, "host": host, 'sites':sites, 'site':site, 'site_description':site_description, 'organization_description': organization_description, 'organizations':organizations, 'organization':organization, "network": network, "network_kind": network_kind, "network_label": network_label})

@wrap_rpc
def add(api, request, network=None, host=None):
	if request.method == 'POST':
		form = NetworkInstanceForm(api, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.resource_create('network_instance',{'host':formData['host'],
										   'bridge':formData['bridge'],
										   'network':formData['network'],
										   'kind':formData['network']})
			return HttpResponseRedirect(reverse("external_network_instances", kwargs={"network": network_id(api, formData['network'])}))
		else:
			return render(request, "form.html", {'form': form, "heading":"Add External Network Instance"})
	else:
		form = NetworkInstanceForm(api)
		if network:
			network = api.resource_info(network)['attrs']['kind']
			form.fields["network"].initial=network
		if host:
			form.fields['host'].initial=host
		return render(request, "form.html", {'form': form, "heading":"Add External Network Instance"})
	
@wrap_rpc
def remove(api, request, res_id=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			res = api.resource_info(res_id)
			api.resource_remove(res_id)
			return HttpResponseRedirect(reverse("external_network_instances", kwargs={"network": network_id(api, res["attrs"]['network'])}))
	form = RemoveConfirmForm.build(reverse("tomato.external_network_instance.remove", kwargs={"res_id": res_id}))
	res = api.resource_info(res_id)
	return render(request, "form.html", {"heading": "Remove External Network Instance", "message_before": "Are you sure you want to remove the external network instance?", 'form': form})	
	

@wrap_rpc
def edit(api, request, res_id = None):
	if request.method=='POST':
		form = EditNetworkInstanceForm(res_id, api, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			if api.resource_info(formData['res_id'])['type'] == 'network_instance':
				api.resource_modify(formData["res_id"],{'host':formData['host'],
														'bridge':formData['bridge'],
														'network':formData['network'],
														'kind':formData['network']}) 
				return HttpResponseRedirect(reverse("external_network_instances", kwargs={"network": network_id(api, formData['network'])}))
			else:
				return render(request, "error/fault.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no external network instance.'})
		else:
			host = request.POST["host"]
			if host:
				return render(request, "form.html", {'form': form, "heading":"Edit External Network Instance on "+host})
			else:
				return render(request, "error/fault.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	else:
		if res_id:
			res_info = api.resource_info(res_id)
			origData = res_info['attrs']
			origData['res_id'] = res_id
			form = EditNetworkInstanceForm(res_id, api, origData)
			return render(request, "form.html", {'form': form, "heading":"Edit External Network Instance on "+res_info['attrs']['host']})
		else:
			return render(request, "error/fault.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})
