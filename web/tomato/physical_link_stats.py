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

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib, settings

def get_site_location(site_name,api):
	
	#return api.site_info(site_name)['geolocation']
	
	if site_name=="ukl":
		return {'longitude':7.768889,'latitude':49.444722}
	if site_name=="tum":
		return {'longitude':11.575278,'latitude':48.136944}
	if site_name=="uwue":
		return {'longitude':9.929444,'latitude':49.794444}
	return {'longitude':0,'latitude':0}

def site_list(api):
	r = []
	for i in api.site_list():
		r.append(i['name'])
	return r

def site_location_list(api):
	r = []
	l = site_list(api)
	for i in l:
		r.append({'name':i,
				  'geolocation':get_site_location(i,api),
				  'displayName':api.site_info(i)['description']})
	return r

def site_site_pairs(api,allow_self=True): # allow_self: allow self-referencing pairs like ('ukl','ukl')
	r = []
	l = site_list(api)
	for i in range(len(l)):
		i_mod = i
		if not (allow_self):
			i_mod = i_mod+1
		for j in range(i_mod,len(l)):
			r.append((l[i],l[j]))
	return r

def site_site_connections(api):
	r = []
	l = site_site_pairs(api,False)
	for i in l:
		src = i[0]
		dst = i[1]
		
		#TODO: add stats
		
		r.append({
			"src":src,
			"dst":dst
			})
	return r

@wrap_rpc
def index(api, request):
	return render_to_response("admin/physical_link_stats/index.html",{'site_location_list':site_location_list(api),'connections': site_site_connections(api),'user':api.account_info()})

