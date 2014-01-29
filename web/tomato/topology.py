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

from django.shortcuts import render, redirect
from django import forms
from django.http import HttpResponse

import json, re

from tutorial import loadTutorial
from lib import wrap_rpc, AuthError

from admin_common import BootstrapForm, Buttons
from tomato.crispy_forms.layout import Layout

class ImportTopologyForm(BootstrapForm):
	topologyfile = forms.FileField(label="Topology File")	
	def __init__(self, *args, **kwargs):
		super(ImportTopologyForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(
			'topologyfile',
			Buttons.default(label="Import")
		)
@wrap_rpc
def list(api, request, show_all=False, organization=None):
	if not api.user:
		raise AuthError()
	toplist=api.topology_list(showAll=show_all, organization=organization)
	orgas=api.organization_list()
	tut_in_top_list = False
	for top in toplist:
		tut_in_top_list_old = tut_in_top_list
		if top['attrs'].has_key('_tutorial_url'):
			top['attrs']['tutorial_url'] = top['attrs']['_tutorial_url']
			tut_in_top_list = True
		if top['attrs'].has_key('_tutorial_disabled'):
			top['attrs']['tutorial_disabled'] = top['attrs']['_tutorial_disabled']
			if top['attrs']['tutorial_disabled']:
				tut_in_top_list = tut_in_top_list_old
	return render(request, "topology/list.html", {'top_list': toplist, 'organization': organization, 'orgas': orgas, 'show_all': show_all, 'tut_in_top_list':tut_in_top_list})

def _display(api, request, info, tut_url, tut_stat):
	caps = api.capabilities()
	res = api.resource_list()
	sites = api.site_list()
	permission_list = api.topology_permissions()
	orgas = dict([(o["name"], o) for o in api.organization_list()])
	for s in sites:
		orga = orgas[s['organization']]
		del s['organization']
		s['organization'] = orga

	tut_data, tut_steps = None, None
	try:
		if tut_url:
			tut_data, tut_steps, _ = loadTutorial(tut_url)
	except:
		pass

	res = render(request, "topology/info.html", {
		'top': info,
		'res_json': json.dumps(res),
		'sites_json': json.dumps(sites),
		'caps_json': json.dumps(caps),
		'tutorial_steps':tut_steps,
		'tutorial_status':tut_stat,
		'tutorial_data': tut_data,
		'permission_list':permission_list,
	})	
	return res


@wrap_rpc
def info(api, request, id): #@ReservedAssignment
	if not api.user:
		raise AuthError()
	info=api.topology_info(id)
	tut_stat = None
	tut_url = None
	allow_tutorial = True
	if info['attrs'].has_key('_tutorial_disabled'):
		allow_tutorial = not info['attrs']['_tutorial_disabled']
	if allow_tutorial:
		if info['attrs'].has_key('_tutorial_url'):
			tut_url = info['attrs']['_tutorial_url']
			if info['attrs'].has_key('_tutorial_status'):
				tut_stat = info['attrs']['_tutorial_status']
	return _display(api, request, info, tut_url, tut_stat);

@wrap_rpc
def usage(api, request, id): #@ReservedAssignment
	if not api.user:
		raise AuthError()
	usage=api.topology_usage(id)
	return render(request, "main/usage.html", {'usage': json.dumps(usage), 'name': 'Topology #%d' % int(id)})

@wrap_rpc
def create(api, request):
	if not api.user:
		raise AuthError()
	info=api.topology_create()
	return redirect("tomato.topology.info", id=info["id"])

@wrap_rpc
def import_(api, request):
	if not api.user:
		raise AuthError()
	if request.method=='POST':
		form = ImportTopologyForm(request.POST,request.FILES)
		if form.is_valid():
			f = request.FILES['topologyfile']			
			topology_structure = json.load(f)
			id_, _, _, errors = api.topology_import(topology_structure)

			if errors != []:
				str = "Errors occured during import";
				for i in errors:
					str = str + "\n " + i
				t = api.topology_info(id_)
				if t['attrs'].has_key('_notes'):
					notes = t['attrs']['_notes']
					if notes:
						str = str + "\n__________\nOriginal Notes:\n" + notes
				api.topology_modify(id_,{'_notes':str,'_notes_autodisplay':True})
				
			return redirect("tomato.topology.info", id=id_)
		else:
			return render(request, "form.html", {'form': form, "heading":"Import Topology"})
	else:
		form = ImportTopologyForm()
		return render(request, "form.html", {'form': form, "heading":"Import Topology"})
		
@wrap_rpc
def export(api, request, id):
	if not api.user:
		raise AuthError()
	top = api.topology_export(id)
	filename = re.sub('[^\w\-_\. ]', '_', id + "__" + top['topology']['attrs']['name'].lower().replace(" ","_") ) + ".tomato3.json"
	response = HttpResponse(json.dumps(top, indent = 2), content_type="application/json")
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response
