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

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page
from django.http import Http404
from django import forms
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib
from admin_common import RemoveResourceForm, is_hostManager


@wrap_rpc
def index(api, request):
    netw_list = api.resource_list('network')
    return render_to_response("admin/external_networks/index.html", {'user': api.user, 'netw_list': netw_list, 'hostManager': is_hostManager(api.account_info())})

@wrap_rpc
def add(api, request):
    return render_to_response("main/error.html",{'user': api.user, 'type':'not implemented yet'})
   
@wrap_rpc
def remove(api, request):
    return render_to_response("main/error.html",{'user': api.user, 'type':'not implemented yet'})

@wrap_rpc
def edit(api, request):
    return render_to_response("main/error.html",{'user': api.user, 'type':'not implemented yet'})
