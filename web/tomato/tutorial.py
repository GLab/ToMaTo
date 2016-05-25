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


from lib import wrap_rpc, security_token
from .lib import anyjson as json
from admin_common import ConfirmForm
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
import uuid
import urllib2, urllib
from urlparse import urljoin

from lib.error import UserError #@UnresolvedImport

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from lib.settings import get_settings, Config
import settings as config_module
settings = get_settings(config_module)



#This is a list of available tutorials (values should be self-explaining):
#'id' references to
# - a tut desc file in ./editor_tutorial/'id'.js
# - a topology file in ./editor_tutorial/'id'.tomato3


@wrap_rpc
def list(api, request):
	tutorial_list_url = settings.get_web_resource_location(Config.WEB_RESOURCE_TUTORIAL_LIST)
	tutorials = json.load(urllib2.urlopen(tutorial_list_url))
	for tut in tutorials:
		for attr in ["icon", "url"]:
			if not attr in tut:
				continue
			tut[attr] = urljoin(tutorial_list_url, tut[attr])
	session_id = uuid.uuid4()
	request.session["id"] = session_id
	return render(request, "topology/tutorials_list.html",{'tutorials':tutorials, 'session_id': session_id})


@wrap_rpc
def start(api, request):
	url = request.REQUEST["url"]
	session_id = request.session.get("id", uuid.uuid4())
	token = request.REQUEST.get("token")
	correct_token = security_token(url, session_id)
	if token != correct_token:
		request.session["id"] = session_id
		form = ConfirmForm.build(reverse("tomato.tutorial.start")+"?"+urllib.urlencode({"token": correct_token, "url": url}))
		return render(request, "form.html", {"heading": "Load tutorial", "message_before": "Are you sure you want to load the tutorial from the following URL? <pre>"+url+"</pre>", 'form': form})

	val = URLValidator()
	
	try: 
		val(url)
		data = json.load(urllib2.urlopen(url))
	except ValidationError:
		return render(request,"topology/tutorial_error.html",{"error_typ":"invalidurl", "error_msg":"Invalid url","url":url})
	except ValueError:
		return render(request,"topology/tutorial_error.html",{"error_typ":"invalidurl", "error_msg":"Invalid url","url":url})
	
	_, _, top_dict, data, _ = loadTutorial(url)
	top_id, _, _, _ = api.topology_import(top_dict)
	api.topology_modify(top_id, {"_tutorial_state": {
																	'enabled': True,
																	'url': url,
													        'step': 0,
													        'data': data
																}
	                             })
	return redirect("tomato.topology.info", id=top_id)

def loadTutorial(url):
	data = json.load(urllib2.urlopen(url))
	steps_str = None
	tut_data = {}
	initscript_str = ""
	if "steps_str" in data:
		steps_str = data["steps_str"]
	if "steps_file" in data:
		steps_url = urljoin(url, data["steps_file"])
		steps_str = urllib2.urlopen(steps_url).read()
	if "topology_data" in data:
		top_dict = data["topology_data"]
	if "topology_file" in data:
		top_url = urljoin(url, data["topology_file"])
		top_dict = json.load(urllib2.urlopen(top_url))
	if "initscript_str" in data:
		initscript_str = data['initscript_str']
	if "initscript_file" in data:
		initscript_url = urljoin(url, data["steps_file"])
		initscript_str = urllib2.urlopen(initscript_url).read()
	if 'initial_data' in data:
		tut_data = data['initial_data']
	data["base_url"] = urljoin(url, data.get("base_url", "."))

		
	return (data, steps_str, top_dict, tut_data, initscript_str)
