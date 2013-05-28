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
from django.shortcuts import render_to_response, redirect
import os, json


#This is a list of available tutorials (values should be self-explaining):
#'id' references to
# - a tut desc file in ./editor_tutorial/'id'.js
# - a topology file in ./editor_tutorial/'id'.tomato3
tutorials = [
                            {
                             'id':   "basic",
                             'name': "Beginner Tutorial",
                             'desc': "Recommended for new users. Teaches the basics about how to use ToMaTo's editor.",
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
    return render_to_response("topology/editor_tutorials_list.html",{'tutorials':tutorials, 'user':api.account_info()})


@wrap_rpc
def loadTutorial(api, request, tut_id):
    
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir,'editor_tutorial/'+tut_id+'.tomato3')
    top_str = open(file_path,'r').read()
    top_dict = json.loads(top_str)
    top_dict['topology']['attrs']['_tutorial_id'] = tut_id
    top_dict['topology']['attrs']['_tutorial_status'] = 0
    top_id, _, _, _ = api.topology_import(top_dict)
    return redirect("tomato.topology.info", id=top_id)