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

import re


#imports a json structure to a topology. returns the new topology's id.
#return structure:
# {'success': True, 'id': <new topologies id>}
# {'success': False, 'message': <error message>}
def import_topology(api, topology_structure):
    
    
    
    #definition of export file version 1:
    #
    #{
    #    file_info:     { version: 1},
    #    elements:     [{
    #                    id: int
    #                    parent: int <reference to other element> [parent<id] | None
    #                    type: str <type of element which is understood by backend>
    #                    attrs: {<attrs for element which are understood by backend>}
    #                    }]
    #    connections: [{
    #                    elements: [ int <reference to an element> ] (length:2)
    #                    attrs: {<attrs for connection which are understood by backend>}
    #                    }]
    #}
    #
    #
    
    def import_v1(api, topo):
        top = topo['topology'].copy()
        top_id = None
        
        try:
            
            top_id = api.topology_create()['id']
            
            name = top['attrs']['name']
            api.topology_modify(top_id,{'name':name})
            
            idMap={} #for every elemnt: it will store the new id for given old ids
                        # (old id = the id stored in the file)
            
            
            elements = sorted(top['elements'], key=lambda el: el['id']) #assumes that for every element, it's parent has a smaller id than itself.
           
            for e in elements:
                el_c = None
                
                #create element
                if e['parent'] is None:
                    el_c = api.element_create(top_id,
                                            e['type'])
                else:
                    par_id = idMap[e['parent']]
                    el_c = api.element_create(top_id,
                                            e['type'],
                                            parent = par_id)
                    
                newElID = el_c['id']
                
                #add attrs; ignore erroneous attrs
                for attr in e['attrs'].keys():
                    try:
                        api.element_modify(newElID,{ attr:e['attrs'][attr] })
                    except:
                        pass
                    
                #remember the new id
                idMap[e['id']] = newElID
                
                        
            
            #add all connections:
            for c in top['connections']:
                el_id0 = idMap[c['elements'][0]]
                el_id1 = idMap[c['elements'][1]]
                
                conn = api.connection_create(el_id0,el_id1)
                newConnID = conn['id']
                for attr in c['attrs'].keys():
                    try:
                        api.connection_modify(newConnID,{attr:c['attrs'][attr]})
                    except:
                        pass
                    
                    
            
        #on error: delete newly created topology:        
        except KeyError as e:
            api.topology_remove(top_id)
            return {'success':False, 'message': 'missing key in file structure: ' + e }
        except:
            api.topology_remove(top_id)
            raise
        
        return {'success':True, 'id':top_id}
    
    
    
    
    
    #check if version info exists in file:
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
        
        blacklist = ['capabilities', 
                     'cap_attrs', 
                     'cap_children', 
                     'cap_actions', 
                     'usage',
                     'host',
                     'host_fileserver_port',
                     'topology',
                     'state']
        
        blacklist_elements = ['children',
                              'connection']
        
        blacklist_connections = ['id']
        
        blacklist_attrs = ['_snap_to_grid',
                           '_fixed_pos']
        
        data = reduceData_rec(data, blacklist)
        data['elements'] = reduceData_rec(data['elements'],blacklist_elements)
        data['connections'] = reduceData_rec(data['connections'],blacklist_connections)
        data['attrs'] = reduceData_rec(data['attrs'], blacklist_attrs)
        
        return data
    

    top_full = api.topology_info(id,True)
    top = reduceData(top_full)
    
    filename = re.sub('[^\w\-_\. ]', '_', id + "__" + top['attrs']['name'].lower().replace(" ","_") ) + ".tomato3"
    
    #attach expandable version information to the file
    return {
            'file_information': {'version': 1, 'original_filename': filename,},
            'topology': top
            }