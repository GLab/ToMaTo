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
	errorgroup = api.errorgroup_list()
	for e in errorgroup:
		e['frontend_mod'] = {'sources':[]}
		for s in e['dump_contents']['source']:
			if s == 'backend':
				e['frontend_mod']['sources'].append('backend')
			if s.startswith('host'):
				e['frontend_mod']['sources'].append('hostmanager')
		 
		
	return render(request, "dumpmanager/list.html", {'errorgroup_list': errorgroup})

@wrap_rpc
def group_info(api, request, group_id):
	errorgroup = api.errorgroup_info(group_id,include_dumps=True)
	return render(request, "dumpmanager/info.html", {'errorgroup': errorgroup})

@wrap_rpc
def group_clear(api,request,group_id):	
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			errordumps = api.errordump_list(group_id)
			for dump in errordumps:
				api.errordump_remove(dump['source'],dump['dump_id'])
			return HttpResponseRedirect(reverse("tomato.dumpmanager.group_info",  kwargs={"group_id": group_id}))
	form = RemoveConfirmForm.build(reverse("tomato.dumpmanager.group_clear", kwargs={"group_id": group_id}))
	group_desc = api.errorgroup_info(group_id, include_dumps=False)['description']
	return render(request, "form.html", {"heading": "Clear Errorgroup", "message_before": "Are you sure you want to clear the errorgroup '"+group_desc+"' from all dumps?", 'form': form})


@wrap_rpc
def group_remove(api, request, group_id):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			errordumps = api.errordump_list(group_id)
			for dump in errordumps:
				api.errordump_remove(dump['source'],dump['dump_id'])
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
		return render(request, "form.html", {"heading": "Editing errorgroup '"+group_id+"'", 'form': form})


@wrap_rpc
def dump_info(api, request, source, dump_id,data=False):
	errordump = api.errordump_info(source, dump_id,data)
	return render(request, "dumpmanager/info.html", {'errordump': errordump})

@wrap_rpc
def dump_remove(api, request, source, dump_id):
	if request.method=='POST':
		form = RemoveConfirmForm(api, request.POST)
		if form.is_valid():
			dump = api.errordump_info(source,dump_id,False)
			api.errordump_remove(source,dump_id)
			return HttpResponseRedirect(reverse("tomato.dumpmanager.group_info",kwargs={'group_id':dump['group_id']}))
	form = RemoveConfirmForm.build(reverse("tomato.dumpmanager.dump_remove", kwargs={"source": source, "dump_id":dump_id}))
	return render(request, "form.html", {"heading": "Remove dump", "message_before": "Are you sure you want to remove the dump '"+dump_id+"' from '"+source+"'?", 'form': form})


@wrap_rpc
def dump_export(api, request, source, dump_id,data=False):
	if not api.user:
		raise AuthError()
	dump = api.errordump_info(source,dump_id,data)
	filename = re.sub('[^\w\-_\. :]', '_', source.lower() + "__" + dump_id ) + ".errordump.json"
	response = HttpResponse(json.orig.dumps(dump, indent = 2), content_type="application/json")
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def dump_export_with_data(request, source, dump_id):
	return dump_export(request, source, dump_id, True)

@wrap_rpc
def refresh(api,request):
	api.errordumps_force_refresh()
	return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))
		