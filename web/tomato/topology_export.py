# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2010 Integrated Communication Systems Lab, University of Kaiserslautern
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

import re

#imports a json structure to a topology. returns the new topology's id.
#return structure:
# {'success': True, 'id': <new topologies id>}
# {'success': False, 'message': <error message>}
def import_topology(api, topology_structure):
    
    def import_v1(api, topo):
        top = topo['topology']
        
                
        
        return {'success':True, 'id':17}
    
    
    
    
    
    #check if version info exists
    if not 'file_information' in topology_structure:
        return {'success': False, 'message': "unknown file structure."}
    inf = topology_structure['file_information']
    if not 'version' in inf:
        return {'success': False, 'message': "unknown file structure."}
    
    
    #check version
    if inf['version'] == 1:
        return import_v1(api,topology_structure)
    
    #if version did not match any known
    return {'success': False, 'message': "unknown file version."}






#exports the given topology to a json structure
def export(api, id):
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
    return {
            'file_information': {'version': 1, 'original_filename': filename,},
            'topology': top
            }