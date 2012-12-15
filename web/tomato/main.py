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

def index(request):
	return render_to_response("main/start.html")

def help(request, page=""):
	if page=="":
		return render_to_response("help/index.html")
	else:
		django.template.loader.get_template("help/pages/"+page+".html")

def ticket(request, page=""):
	return HttpResponseRedirect(settings.ticket_url % page)

def project(request, page=""):
	return HttpResponseRedirect(settings.project_url % page)

def logout(request):
	if "auth" in request.session:
		del request.session["auth"]
	return HttpResponseNotAuthorized(code=401, text="You have been logged out.")

