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

import os
from django.shortcuts import redirect

def dynimg(request,size,objtype,arg1,arg2):
	"""
	Uses 2 arguments to build a path to an image file for a specific object type. It then checks whether this image file exists. On success, it redirects to this file. If it does not exist, it redirects to a generic image file for this object type.
	for templates: tech/size/subtype/name
	for networks:  network/size/kind/none
	for vpns:	  vpn/size/kind/none
	"""
	filepath_pref = ""
	url_alt = ""
	
	
	# handle devices
	if objtype=="openvz" or objtype=="kvmqm" or objtype=="repy":
		subtype=arg1
		template_name=arg2
		
		#handle non-(repy-network) devices
		if objtype!="repy" or subtype=="device":
			found_templ = False
			for i in ['floodlight']:
				if i in template_name:
					template_name = i
					found_templ = True
			#if the template is known, first try to find a template-specific image. On error, redirect to a non-template dynimg url
			if found_templ:
				filepath_pref="img/"+objtype+"_"+template_name+size+".png"
				url_alt = "/dynimg/"+objtype+"/"+size+"/"+subtype+"/none"
			#if the template is not known, try to match the subtype
			else:
				filepath_pref="img/"+objtype+"_"+subtype+size+".png"
				url_alt ="/img/"+objtype+size+".png"
		# handle repy network devices
		else:
			filepath_pref="img/switch_repy32.png"
			url_alt="/img/network32.png"
		
	# handle networks
	elif objtype=="network" or objtype=="vpn":
		kind=arg1
		for i in ["openflow"]:
			if i in kind:
				kind = i
		filepath_pref="img/"+kind+size+".png"
		url_alt="/img/"+objtype+size+".png"
		
	# handle everything else
	else:
		filepath_pref="img/"+objtype+size+".png"
		url_alt="/img/"+objtype+".png"
		
		
	# now, check whether the file exists and redirect to the preferred or alternate url
	url_pref="/"+filepath_pref
	prefix = os.path.dirname(os.path.realpath(__file__))
	if os.path.exists(os.path.join(prefix, filepath_pref)):
		return redirect(url_pref)
	else:
		return redirect(url_alt)
		
	