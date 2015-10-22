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
from lib import wrap_rpc, api_duration_log

@wrap_rpc
def host_users(api, request, name):
	users = api.host_users(name)
	return render(request, "debug/host_users.html", {'host': name, 'users': users})

@wrap_rpc
def topology(api, request, id):
	data = api.topology_info(id, True)
	return render(request, "debug/json.html", {'title': "Information on topology #%s" % id, 'data': data})

@wrap_rpc
def element(api, request, id):
	data = api.element_info(id)
	return render(request, "debug/json.html", {'title': "Information on element #%s" % id, 'data': data})

@wrap_rpc
def connection(api, request, id):
	data = api.connection_info(id)
	return render(request, "debug/json.html", {'title': "Information on connection #%s" % id, 'data': data})

@wrap_rpc
def stats(api, request):
	stats = api.debug_stats()
	return render(request, "debug/stats.html", {'stats': stats})

def api_call_stats(request):
	original_data = api_duration_log().get_api_durations()
	data = []
	for name, values in original_data.iteritems():
		data.append([name, values['duration']])

	return render(request, "debug/table.html", {'title': "API duration log", 'data': data, 'table_headings': ['Function', 'Duration (s)']})
