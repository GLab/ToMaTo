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

import re, time
from .lib import anyjson as json

from tutorial import loadTutorial
from web_resources import web_resources
from lib import wrap_rpc, AuthError, serverInfo

from admin_common import BootstrapForm, Buttons
from tomato.crispy_forms.layout import Layout

from settings import default_executable_archives_list_url


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
	toplist = api.topology_list(showAll=show_all, organization=organization)
	orgas = api.organization_list()
	for top in toplist:
		"""top['attrs']['tutorial_enabled'] = (
											   top['attrs'].has_key('_tutorial_url') and not (
											   top['attrs']['_tutorial_disabled'] if top['attrs'].has_key(
												   '_tutorial_disabled') else False)  # old tutorials
										   ) or (
											   top['attrs']['_tutorial_state']['enabled'] if (
											   top['attrs'].has_key('_tutorial_state') and top['attrs'][
												   '_tutorial_state'].has_key('enabled')) else top['attrs'].has_key(
												   '_tutorial_state')  # new tutorials
										   )
		"""
		top["tutorial_enabled"] = top.has_key('_tutorial_state') and \
															top['_tutorial_state'].get('enabled', False)

		top['processed'] = {
		'timeout_critical': top['timeout'] - time.time() < serverInfo()['topology_timeout']['warning']}
	return render(request, "topology/list.html",
		{'top_list': toplist, 'organization': organization, 'orgas': orgas, 'show_all': show_all})



def _display(api, request, info, tutorial_state):
	caps = api.capabilities()
	resources = api.resources_map()
	sites = api.site_list()
	permission_list = api.topology_permissions()
	orgas = dict([(o["name"], o) for o in api.organization_list()])
	for s in sites:
		orga = orgas[s['organization']]
		del s['organization']
		s['organization'] = orga

	tut_data, tut_steps, initscript = None, None, None
	try:
		if tutorial_state['url']:
			tut_data, tut_steps, _, _, initscript = loadTutorial(tutorial_state['url'])
	except:
		pass

	editor_size_scale =  2 if ("_big_editor" in info and info['_big_editor']) else 1
	editor_size = {
		'width': int(800 * editor_size_scale),
		'height':int(600 * editor_size_scale)
	}
	editor_size['marginleft'] = int( (800-editor_size['width']) / 2 )

	res = render(request, "topology/info.html", {
		'top': info,
		'timeout_settings': serverInfo()["topology_timeout"],
		'res_json': json.dumps(resources),
		'res_web_json': json.dumps(web_resources()),
		'sites_json': json.dumps(sites),
		'caps_json': json.dumps(caps),
		'tutorial_info':{'state': tutorial_state,
						 'steps':tut_steps,
						 'data': tut_data,
						 'initscript': initscript},
		'permission_list':permission_list,
		'editor': {
			'size': editor_size
		}
	})	
	return res


@wrap_rpc
def info(api, request, id):  # @ReservedAssignment
	if not api.user:
		raise AuthError()
	info = api.topology_info(id)

	#Load Tutorial.
	tutorial_state = {'enabled': False}
	if info.has_key('_tutorial_state'):
		tutorial_state = info['_tutorial_state']

	return _display(api, request, info, tutorial_state);


@wrap_rpc
def create(api, request):
	if not api.user:
		raise AuthError()
	info = api.topology_create()
	api.topology_modify(info['id'], {'_initialized': False})
	return redirect("tomato.topology.info", id=info["id"])


@wrap_rpc
def import_(api, request):
	if not api.user:
		raise AuthError()
	if request.method == 'POST':
		form = ImportTopologyForm(request.POST, request.FILES)
		if form.is_valid():
			f = request.FILES['topologyfile']
			topology_structure = json.load(f)
			id_, _, _, errors = api.topology_import(topology_structure)
			api.topology_modify(id_, {'_initialized': True})
			if errors != []:
				errors = ["%s %s: failed to set %s=%r, %s" % (type_, cid, key, val, err) for type_, cid, key, val, err
					in errors]
				note = "Errors occured during import:\n\n" + "\n\n".join(errors)
				t = api.topology_info(id_)
				if t.has_key('_notes') and t['_notes']:
					note += "\n__________\nOriginal Notes:\n" + t['_notes']
				api.topology_modify(id_, {'_notes': note, '_notes_autodisplay': True})
			return redirect("tomato.topology.info", id=id_)
		else:
			return render(request, "form.html", {'form': form, "heading": "Import Topology",
			'message_before': "Here you can import a topology file which you have previously exported from the Editor."})
	else:
		form = ImportTopologyForm()
		return render(request, "form.html", {'form': form, "heading": "Import Topology",
		'message_before': "Here you can import a topology file which you have previously exported from the Editor."})


@wrap_rpc
def export(api, request, id):
	if not api.user:
		raise AuthError()
	top = api.topology_export(id)
	filename = re.sub('[^\w\-_\. ]', '_',
		top['topology']['name'].lower().replace(" ", "_")) + "__" + id + ".tomato4.json"
	response = HttpResponse(json.orig.dumps(top, indent=2), content_type="application/json")
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response
