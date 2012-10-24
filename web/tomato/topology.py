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

from django.shortcuts import render_to_response

import json

from lib import wrap_rpc

@wrap_rpc
def index(api, request):
	toplist=api.topology_list()
	return render_to_response("topology/index.html", {'top_list': toplist})

def _display(api, info):
	if info["elements"] and isinstance(info["elements"][0], int):
		info = api.topology_info(id, full=True)
	res = api.resource_list()
	sites = api.site_list()
	return render_to_response("topology/info.html", {'top': info, 'top_json': json.dumps(info), 'res_json': json.dumps(res), 'sites_json': json.dumps(sites)})	

@wrap_rpc
def info(api, request, id): #@ReservedAssignment
	info=api.topology_info(id, full=True)
	return _display(api, info);

@wrap_rpc
def usage(api, request, id): #@ReservedAssignment
	usage=api.topology_usage(id)
	return render_to_response("main/usage.html", {'usage': json.dumps(usage), 'name': 'Topology #%d' % int(id)})

@wrap_rpc
def create(api, request):
	info=api.topology_create()
	return _display(api, info)

@wrap_rpc
def import_form(api, request):
	return index(request)