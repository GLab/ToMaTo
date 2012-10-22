# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2012 Integrated Communication Systems Lab, University of Kaiserslautern
#
# This file is part of the ToMaTo project
#
# ToMaTo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import Http404
from django import forms
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib

class AddSiteForm(forms.Form):
    name = forms.CharField(max_length=50)
    description = forms.CharField(max_length=255)


@wrap_rpc
def index(api, request):
    #
    #
    # DUMMY
    # showRemove: check for remove privileges
    #
    #
    showRemove = True
    return render_to_response("admin/site/index.html", {'site_list': api.site_list(), 'showRemove': showRemove})

@wrap_rpc
def add(api, request):
    #
    # NOT FULLY IMPLEMENTED
    # check for duplicates
    # length of form fields (AddSiteForm)
    #
    if request.method == 'POST':
        form = AddSiteForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if formData["name"]: #At this point, check if trying to add a duplicate.
                api.site_create(formData["name"],formData["description"])
                return render_to_response("admin/site/add_success.html", {'name': formData["name"]})
            else:
                return render_to_response("admin/site/add_form.html", {'form': form, 'action':request.path})
        else:
            return render_to_response("admin/site/add_form.html", {'form': form, 'action':request.path})
    else:
        form = AddSiteForm
        return render_to_response("admin/site/add_form.html", {'form': form, 'action':request.path})
    
@wrap_rpc
def remove(api, request):
    #
    #
    #   DUMMY
    #
    #
    showRemove = True
    return render_to_response("admin/site/index.html", {'site_list': api.site_list(), 'showRemove': showRemove})