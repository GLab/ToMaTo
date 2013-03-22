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
	#	file_info:	 { version: 1},
	#	elements:	 [{
	#					id: int
	#					parent: int <reference to other element> | None
	#					type: str <type of element which is understood by backend>
	#					attrs: {<attrs for element which are understood by backend>}
	#					}]
	#	connections: [{
	#					elements: [ int <reference to an element> ] (length:2)
	#					attrs: {<attrs for connection which are understood by backend>}
	#					}]
	#}
	#
	#
	
	def import_v1(api, topo):
		top = topo['topology'].copy()
		top_id = None
		elementIds = {}   
		connectionIds = {}   
		try:
			top_id = api.topology_create()['id']
			for key, value in top['attrs'].iteritems():
				try:
					api.topology_modify(top_id, {key: value})
				except:
					print "Failed to set topology attribute %s to %s" % (key, value)
					
			elements = top["elements"]
			elements.sort(key=lambda el: el['id'])
			
			for el in elements:
				parentId = elementIds.get(el.get('parent'))
				elId = api.element_create(top_id, el['type'], parent=parentId)['id']
				elementIds[el['id']] = elId
				for key, value in el['attrs'].iteritems():
					try:
						api.element_modify(elId, {key: value})
					except:
						print "Failed to set element attribute %s to %s" % (key, value)
				
			for con in top["connections"]:
				el1 = elementIds.get(con["elements"][0])
				el2 = elementIds.get(con["elements"][1])
				conId = api.connection_create(el1, el2)['id']
				connectionIds[con['id']] = conId
				for key, value in con['attrs'].iteritems():
					try:
						api.connection_modify(conId, {key: value})
					except:
						print "Failed to set connection attribute %s to %s" % (key, value)
					
		except:
			api.topology_remove(top_id)
			raise
		
		return (top_id, elementIds, connectionIds)
	
	
	
	
	
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
		
		blacklist = ['usage', 'debug', 'bridge', 'capture_port', 'websocket_pid', 'vmid', 'vncpid',
					 'host', 'websocket_port', 'vncport', 'peers', 'pubkey', 'path', 'port', 
					 'host_fileserver_port',
					 'topology',
					 'state']
		
		blacklist_elements = ['children',
							  'connection']
		
		blacklist_connections = []
		
		blacklist_attrs = []
		
		data = reduceData_rec(data, blacklist)
		data['elements'] = reduceData_rec(data['elements'],blacklist_elements)
		data['connections'] = reduceData_rec(data['connections'],blacklist_connections)
		data['attrs'] = reduceData_rec(data['attrs'], blacklist_attrs)
		
		return data
	

	top_full = api.topology_info(id,True)
	top = reduceData(top_full)
	
	#attach expandable version information to the file
	return {
			'file_information': {'version': 1},
			'topology': top
			}