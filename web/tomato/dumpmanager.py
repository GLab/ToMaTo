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

import re, time

from django.shortcuts import render
from django import forms
from lib import wrap_rpc, AuthError, wrap_json
from .lib import anyjson as json
from django.http import HttpResponseRedirect, HttpResponse

from admin_common import BootstrapForm, RemoveConfirmForm, Buttons
from tomato.crispy_forms.layout import Layout
from django.core.urlresolvers import reverse

from lib.error import UserError #@UnresolvedImport
from lib.github import create_issue as create_github_issue, is_enabled as github_enabled

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
	description = forms.CharField(max_length=255,help_text="A description of the error to identify it.")
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
	errorgroup['github_url'] = errorgroup.get('_github_url', False)
	return render(request, "dumpmanager/info.html", {'errorgroup': errorgroup, 'github_enabled': github_enabled()})

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
		return render(request, "form.html", {"heading": "Renaming Error Group '"+errorgroupinfo['description']+"'", 'form': form})


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
def _remove_old_errors(api, request, border_time, delete):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			errorgroups = api.errorgroup_list()
			for group in errorgroups:
				if group['last_timestamp'] < time.time() - border_time*60*60*24:
					if delete:
						api.errorgroup_remove(group['group_id'])
					else:
						api.errorgroup_hide(group['group_id'])
			return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))
	reverse_target = "tomato.dumpmanager.remove_old_errorgroups" if delete else "tomato.dumpmanager.hide_old_errorgroups"
	heading = "%s Old Error Groups" % ("Remove" if delete else "Clear")
	message_before = "Are you sure you want to %s all error groups%s?"
	message_before = message_before % ("remove" if delete else "clear",
																		(" with no dumps younger than %s day%s" % (str(border_time), "" if border_time==1 else "s") if border_time!=0 else ""))
	form = RemoveConfirmForm.build(reverse(reverse_target, kwargs={'border_time': border_time}))
	return render(request, "form.html", {"form": form, "heading": heading, "message_before": message_before})

def remove_old_errorgroups(request, border_time):
	return _remove_old_errors(request, float(border_time), True)

def hide_old_errorgroups(request, border_time):
	return _remove_old_errors(request, float(border_time), False)

@wrap_rpc
def errorgroup_favorite(api, request, group_id):
	api.errorgroup_favorite(group_id, True)
	return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))

@wrap_rpc
def errorgroup_unfavorite(api, request, group_id):
	api.errorgroup_favorite(group_id, False)
	return HttpResponseRedirect(reverse("tomato.dumpmanager.group_list"))

@wrap_json
def errorgroup_github(api, request, group_id):
	info = api.errorgroup_info(group_id, include_dumps=False)
	if "_github_url" not in info:

		info = api.errorgroup_info(group_id, include_dumps=True)
		dump_tofetch = info['dumps'][0]
		for dump in info['dumps']:
			if dump['data_available']:
				dump_tofetch = dump
		dump_info = api.errordump_info(group_id, dump_tofetch['source'], dump_tofetch['dump_id'], include_data=True)

		backend_dump = False
		host_dump = 0
		for source in info['dump_contents']['source']:
			if source == "backend":
				backend_dump = True
			elif source.startswith('host'):
				host_dump += 1
		source_str = []
		source_str_short = []
		if backend_dump:
			source_str.append('Backend')
			if host_dump:
				source_str.append(' and ')
		if host_dump:
			source_str.append('%s Hostmanager%s' % (str(host_dump), "s" if host_dump>1 else ""))

		issue_title = info['description']
		trace = []
		for filename, line, function, body in dump_info['data'].get("exception", {}).get("trace", []):
			trace.append("""%s, line %s, in %s
 %s""" % (filename, line, function, body))
		trace_str = """

""".join(trace)
		body_info = ("".join(source_str),
							request.build_absolute_uri(reverse(group_info, kwargs={'group_id': group_id})),
							dump_info['description'],
							trace_str)
		issue_body = """Happened on %s

[View in Dump Manager](%s)

Description:
```
%s
```
Trace:
```
%s
```""" % body_info

		issue = create_github_issue(issue_title, issue_body)

		info = api.errorgroup_modify(group_id, {'_github_url': issue.html_url})

	return info['_github_url']
