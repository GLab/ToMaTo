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

from django.shortcuts import render_to_response, redirect
from django import forms
from django.http import HttpResponse
import re

import json

from lib import wrap_rpc

class ImportTopologyForm(forms.Form):
    topologyfile  = forms.FileField(label="Topology File")    
    
@wrap_rpc
def index(api, request):
    toplist=api.topology_list()
    return render_to_response("topology/index.html", {'user': api.user, 'top_list': toplist})

def _display(api, info):
    res = api.resource_list()
    sites = api.site_list()
    return render_to_response("topology/info.html", {'user': api.user, 'top': info, 'res_json': json.dumps(res), 'sites_json': json.dumps(sites), 'beginner_mode': json.dumps(api.user.get("tutorial", True))})	

@wrap_rpc
def info(api, request, id): #@ReservedAssignment
    info=api.topology_info(id)
    return _display(api, info);

@wrap_rpc
def usage(api, request, id): #@ReservedAssignment
    usage=api.topology_usage(id)
    return render_to_response("main/usage.html", {'user': api.user, 'usage': json.dumps(usage), 'name': 'Topology #%d' % int(id)})

@wrap_rpc
def create(api, request):
    info=api.topology_create()
    return redirect("tomato.topology.info", id=info["id"])

@wrap_rpc
def import_form(api, request):
    if request.method=='POST':
        form = ImportTopologyForm(request.POST,request.FILES)
        if form.is_valid():
            f = request.FILES['topologyfile']
            
            #TODO this is a stub: use f to handle the imported file.
            # Documentation of what to do with f: https://docs.djangoproject.com/en/dev/topics/http/file-uploads/?from=olddocs#handling-uploaded-files
            
        else:
            return render_to_response("topology/import_form.html", {'user': api.user, 'form': form})
    else:
        form = ImportTopologyForm()
        return render_to_response("topology/import_form.html", {'user': api.user, 'form': form})
        
        
@wrap_rpc
def export(api, request, id):
    
    def reduceData(data):
        def reduceData_rec(data, blacklist):
            if isinstance(data, list):
                return [reduceData_rec(el, blacklist) for el in data]
            if isinstance(data, dict):
                return dict(filter(lambda (k, v): k not in blacklist, [(k, reduceData_rec(v, blacklist)) for k, v in data.iteritems()]))
            return data
        
        del data['id']
        del data['permissions']
        del data['attrs']['_snap_to_grid']
        del data['attrs']['_fixed_pos']
        
        blacklist = ['capabilities', 
                     'cap_attrs', 
                     'cap_children', 
                     'cap_actions', 
                     'usage',
                     'host',
                     'host_fileserver_port',
                     'topology',
                     'state']
        
        data = reduceData_rec(data, blacklist)
        
        return data
    

    top_full = api.topology_info(id,True)
    top = reduceData(top_full)
    
    filename = re.sub('[^\w\-_\. ]', '_', id + "__" + top['attrs']['name'].lower().replace(" ","_") ) + ".tomato3"
    
    #attach expandable version information to the file
    return_obj = {
                  'file_information': {'version': 1},
                  'topology': top
                  }
    
    response = HttpResponse(json.dumps(return_obj, indent = 2), content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
    
    return response
    