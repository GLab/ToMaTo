# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2013 Integrated Communication Systems Lab, University of Kaiserslautern
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


from lib import wrap_rpc
from django.shortcuts import render, redirect
import json
import urllib2
from urlparse import urljoin
from django.http import HttpResponse


#This is a list of available tutorials (values should be self-explaining):
#'id' references to
# - a tut desc file in ./editor_tutorial/'id'.js
# - a topology file in ./editor_tutorial/'id'.tomato3
tutorials = [
							{
							 'id':   "chat",
							 'name': "Chat Tutorial",
							 'desc': "Get an overview over ToMaTo and its major features in a scenario using a text-based chat client.",
							 'icon': "/img/user32.png"
							},
							{
							 'id':   "basic",
							 'name': "Beginner Tutorial",
							 'desc': "Teaches the basics about how to use ToMaTo's editor.",
							 'icon': "/img/user32.png"
							},
							{
							 'id':   "data_access",
							 'name': "Data Access",
							 'desc': "Teaches various methods on how to upload and/or download data to/from the devices",
							 'icon': "/img/download.png"
							},
							{
							 'id':   "connections",
							 'name': "Using Connections",
							 'desc': "Learn everything about connections. (currently under construction)",
							 'icon': "/img/connect32.png"
							}
							#===================================================
							# {
							# 'id':   "devices",
							# 'name': "Using Devices",
							# 'desc': "Learn everything about devices.",
							# 'icon': "/img/openvz32.png"
							# }
							#===================================================
			 
			]


@wrap_rpc
def index(api, request):
	return render(request, "topology/editor_tutorials_list.html",{'tutorials':tutorials})


@wrap_rpc
def start(api, request):
	url = request.REQUEST["url"]
	_, _, top_dict = loadTutorial(url)
	top_dict['topology']['attrs']['_tutorial_url'] = url
	top_dict['topology']['attrs']['_tutorial_status'] = 0
	top_id, _, _, _ = api.topology_import(top_dict)
	return redirect("tomato.topology.info", id=top_id)

def loadTutorial(url):
	data = json.load(urllib2.urlopen(url))
	steps_str = None
	if "steps_str" in data:
		steps_str = data["steps_str"]
	if "steps_file" in data:
		steps_url = urljoin(url, data["steps_file"])
		steps_str = urllib2.urlopen(steps_url).read()
	if "topology_str" in data:
		top_dict = json.loads(data["topology_data"])
	if "topology_file" in data:
		top_url = urljoin(url, data["topology_file"])
		top_dict = json.load(urllib2.urlopen(top_url))
	data["base_url"] = urljoin(url, data.get("base_url", "."))
	return (data, steps_str, top_dict)