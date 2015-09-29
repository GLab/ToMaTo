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

import re

from django.shortcuts import render
from django import forms
from lib import wrap_rpc, AuthError
from .lib import anyjson as json
from django.http import HttpResponseRedirect, HttpResponse

from admin_common import BootstrapForm, RemoveConfirmForm, Buttons
from tomato.crispy_forms.layout import Layout
from django.core.urlresolvers import reverse

from lib.error import UserError #@UnresolvedImport

class ErrorDumpForm(BootstrapForm):
	source = forms.CharField(max_length=255,help_text="The description for the errorgroup. This is also its name in the errorgroup list.", widget=forms.HiddenInput())
	dump_id = forms.CharField(max_length=255,help_text="The description for the errorgroup. This is also its name in the errorgroup list.", widget=forms.HiddenInput())
	buttons = Buttons.cancel_add
	def __init__(self, api, *args, **kwargs):
		super(ErrorDumpForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(
			'source',
			'dump_id',
			self.buttons
		)
	
class ErrorGroupForm(BootstrapForm):
	description = forms.CharField(max_length=255,help_text="The description for the errorgroup. This is also its name in the errorgroup list.")
	buttons = Buttons.cancel_add
	def __init__(self, api, *args, **kwargs):
		super(ErrorGroupForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(
			'description',
			self.buttons
		)
	
class EditErrorGroupForm(ErrorGroupForm):
	buttons = Buttons.cancel_save
	def __init__(self, api, group_id, *args, **kwargs):
		super(EditErrorGroupForm, self).__init__(api, *args, **kwargs)
		self.helper.form_action = reverse(group_edit, kwargs={"group_id": group_id})
	

@wrap_rpc
def group_list(api, request, site=None, organization=None):	
	errorgroups = api.errorgroup_list()
	for e in errorgroups:
		e['frontend_mod'] = {'sources':[]}
		host_count = 0
		for s in e['dump_contents']['source']:
			if s == 'backend':
				e['frontend_mod']['sources'].append('backend')
			if s.startswith('host'):
				host_count+=1
		if host_count>0:
			if len(e['frontend_mod']['sources'])>0:
				e['frontend_mod']['sources'].append(", ")
			e['frontend_mod']['sources'].append('%d hostmanager' % host_count)

	favorite_groups = []
	other_groups = []
	for group in errorgroups:
		if group['user_favorite']:
			favorite_groups.append(group)
		else:
			other_groups.append(group)

	favorite_groups.sort(key=lambda e: e['last_timestamp'], reverse=True)
	other_groups.sort(key=lambda e: e['last_timestamp'], reverse=True)
	lists = [(favorite_groups, True), (other_groups, False)]

	if favorite_groups or other_groups:
		is_empty = False
	else:
		is_empty = True

	return render(request, "dumpmanager/list.html", {'errorgroup_lists': lists, 'is_empty': is_empty})

@wrap_rpc
def group_info(api, request, group_id):
	errorgroup = api.errorgroup_info(group_id, include_dumps=True)
	for errordump in errorgroup['dumps']:
		errordump['source___link'] = None
		if errordump['source'].startswith('host:'):
			errordump['source___link'] = errordump['source'].replace('host:', '')
	errorgroup['dumps'].sort(key=lambda d: d['timestamp'])
	return render(request, "dumpmanager/info.html", {'errorgroup': errorgroup})

@wrap_rpc
def group_hide(api,request,group_id):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.errorgroup_hide(group_id)
			return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))
	form = RemoveConfirmForm.build(reverse("tomato.dumpmanager.group_hide", kwargs={"group_id": group_id}))
	group_desc = api.errorgroup_info(group_id, include_dumps=False)['description']
	return render(request, "form.html", {"heading": "Clear Errorgroup", "message_before": "Are you sure you want to clear the errorgroup '"+group_desc+"' from all dumps?", 'form': form})


@wrap_rpc
def group_remove(api, request, group_id):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.errorgroup_remove(group_id)
			return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))
	form = RemoveConfirmForm.build(reverse("tomato.dumpmanager.group_remove", kwargs={"group_id": group_id}))
	group_desc = api.errorgroup_info(group_id, include_dumps=False)['description']
	return render(request, "form.html", {"heading": "Remove Errorgroup", "message_before": "Are you sure you want to remove the errorgroup '"+group_desc+"'?", 'form': form})

@wrap_rpc
def group_edit(api, request, group_id):
	if request.method=='POST':
		form = ErrorGroupForm(api, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.errorgroup_modify(group_id,{"description": formData["description"]})
			return HttpResponseRedirect(reverse("tomato.dumpmanager.group_info", kwargs={"group_id": group_id}))
		if not group_id:
			group_id=request.POST["group_id"]
		UserError.check(group_id, UserError.INVALID_DATA, "Form transmission failed.")
		return render(request, "form.html", {"heading": "Editing errorgroup '"+group_id+"'", 'form': form})
	else:
		UserError.check(group_id, UserError.INVALID_DATA, "No error group specified.")
		errorgroupinfo=api.errorgroup_info(group_id,False)
		form = EditErrorGroupForm(api, group_id, errorgroupinfo)
		return render(request, "form.html", {"heading": "Renaming errorgroup '"+errorgroupinfo['description']+"'", 'form': form})


@wrap_rpc
def dump_info(api, request, source, dump_id,data=False):
	errordump = api.errordump_info(source, dump_id,data)
	return render(request, "dumpmanager/info.html", {'errordump': errordump})

@wrap_rpc
def dump_export(api, request, group_id, source, dump_id, data=False):
	if not api.user:
		raise AuthError()
	dump = api.errordump_info(group_id, source, dump_id,data)
	filename = re.sub('[^\w\-_\. :]', '_', source.lower() + "__" + dump_id ) + ".errordump.json"
	response = HttpResponse(json.orig.dumps(dump, indent = 2), content_type="application/json")
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def dump_export_with_data(request, group_id, source, dump_id):
	return dump_export(request, group_id, source, dump_id, True)

@wrap_rpc
def refresh(api,request):
	api.errordumps_force_refresh()
	return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))

@wrap_rpc
def errorgroup_favorite(api, request, group_id):
	api.errorgroup_favorite(group_id, True)
	return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))

@wrap_rpc
def errorgroup_unfavorite(api, request, group_id):
	api.errorgroup_favorite(group_id, False)
	return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))
