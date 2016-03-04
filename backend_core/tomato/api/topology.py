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

from api_helpers import _getCurrentUserInfo, _getCurrentUserName
from ..authorization import get_topology_info as _get_topology_info, get_user_info as _get_user_info
from ..lib.topology_role import role_descriptions as _role_descriptions

def _getTopology(id_):
	top = topology.get(id_)
	UserError.check(top, code=UserError.ENTITY_DOES_NOT_EXIST, message="Topology with that id does not exist", data={"id": id_})
	return top

def topology_create():
	"""
	Creates an empty topology.
	
	Return value:
	  The return value of this method is the info dict of the new topology as
	  returned by :py:func:`topology_info`. This info dict also contains the
	  topology id that is needed for further manipulation of that object.
	"""
	_getCurrentUserInfo().check_may_create_topologies()
	return topology.create().info()

def topology_permissions():
	return _role_descriptions()

def topology_remove(id): #@ReservedAssignment
	"""
	Removes and empty topology.
	
	Return value:
	  The return value of this method is ``None``.
	  
	Exceptions:
	  The topology must not contain elements or connections, otherwise the call
	  will fail.
	"""
	_getCurrentUserInfo().check_may_remove_topology(_get_topology_info(id))
	top = _getTopology(id)
	top.remove()

def topology_modify(id, attrs): #@ReservedAssignment
	"""
	Modifies a topology, configuring it with the given attributes.
   
	Currently the only supported attribute for topologies is ``name``.
   
	Additional to the attributes that are supported by the topology,
	all attributes beginning with an underscore (``_``) will be accepted.
	This can be used to store addition information needed by a frontend.
	
	Parameter *id*:
	  The parameter *id* identifies the topology by giving its unique id.
	 
	Parameter *attrs*:
	  The attributes of the topology can be given as the parameter *attrs*. 
	  This parameter must be a dict of attributes.
	
	Return value:
	  The return value of this method is the info dict of the topology as 
	  returned by :py:func:`topology_info`. This info dict will reflect all
	  attribute changes.	
	"""
	_getCurrentUserInfo().check_may_modify_topology(_get_topology_info(id))
	top = _getTopology(id)
	top.modify(attrs)
	return top.info()

def topology_action(id, action, params=None): #@ReservedAssignment
	"""
	Performs an action on the whole topology (i.e. on all elements) in a smart
	way.
	
	The following actions are currently supported by topologies:
	
	  ``prepare``
		This action will execute the action ``prepare`` on all elements in the 
		state ``created``.
	  
	  ``destroy``
		This action will first execute the action ``stop`` on all elements in 
		the state ``started`` and then the action ``destroy`` on all elements 
		in the state ``prepared``.
		Note that the states of the elements will be re-evaluated after the 
		first round of actions.

	  ``start``
		This action will first execute the action ``prepare`` on all elements
		in the state ``created`` and then the action ``start`` on all elements
		in the state ``prepared``.
		Note that the states of the elements will be re-evaluated after the 
		first round of actions.
	  
	  ``stop``
		This action will execute the action ``stop`` on all elements in the 
		state ``started``.
		
	Parameter *id*:
	  The parameter *id* identifies the topology by giving its unique id.

	Parameter *action*:
	  The parameter *action* is the action to execute on the topology.
	 
	Parameter *params*:
	  The parameters for the action (if needed) can be given as the parameter
	  *params*. This parameter must be a dict if given.
	
	Return value:
	  The return value of this method is  **not the info dict of the 
	  topology**. Instead this method returns the result of the action. Changes
	  of the action to the topology can be checked using 
	  :py:func:`~topology_info`.	
	"""
	_getCurrentUserInfo().check_may_run_topology_action(_get_topology_info(id), action)
	if not params: params = {}
	top = _getTopology(id)
	return top.action(action, params)

def topology_info(id, full=False): #@ReservedAssignment
	"""
	Retrieves information about a topology.
	
	Parameter *id*:
	  The parameter *id* identifies the topology by giving its unique id.

	Parameter *full*:
	  If this parameter is ``True``, the fields ``elements`` and 
	  ``connections`` will be a list holding all information of 
	  :py:func:`~backend.tomato.api.elements.element_info`
	  and :py:func:`~backend.tomato.api.connections.connection_info`
	  for each component.
	  Otherwise these fields will be lists holding only the ids of the
	  respective objects.

	Return value:
	  The return value of this method is a dict containing information
	  about this topology:

	``id``
	  The unique id of the topology.
	  
	``elements``
	  A list with all elements. Depending on the parameter *full* this list
	  includes the full information of the elements as given by 
	  :py:func:`~backend.tomato.api.element.element_info` or only the id of the
	  element.

	``connections``
	  A list with all connections. Depending on the parameter *full* this list
	  includes the full information of the connections as given by 
	  :py:func:`~backend.tomato.api.connection.connection_info` or only the id
	  of the connection.
	  
	``attrs``
	  A dict of attributes of this topology. If this topology does not have
	  attributes, this field is ``{}``.	

	``usage``
	  The latest usage record of the type ``5minutes``. See 
	  :doc:`/docs/accountingdata` for the contents of the field.

	``permissions``
	  A dict with usernames as the keys and permission levels as values.
	"""
	_getCurrentUserInfo().check_may_view_topology(_get_topology_info(id))
	top = _getTopology(id)
	return top.info(full)

def topology_list(full=False, showAll=False, organization=None): #@ReservedAssignment
	"""
	Retrieves information about all topologies the user can access.

	Parameter *full*:
	  See :py:func:`~topology_info` for this parameter.
	 
	Return value:
	  A list with information entries of all topologies. Each list entry
	  contains exactly the same information as returned by 
	  :py:func:`topology_info`. If no topologies exist, the list is empty. 
	"""
	if organization:
		_getCurrentUserInfo().check_may_list_organization_topologies(organization)
		organization = _getOrganization(organization)
		users = getAllUsers(organization)
		tops = topology.getAll(permissions__user__in=users, permissions__role="owner")
	elif showAll:
		_getCurrentUserInfo().check_may_list_all_topologies()
		tops = topology.getAll()
	else:
		tops = topology.getAll(permissions__user=_getCurrentUserName())
	return [top.info(full) for top in filter(lambda t:t.hasRole("user"), tops)]

def topology_permission(id, user, role): #@ReservedAssignment
	"""
	Grants/changes permissions for a user on a topology. See :doc:`permissions`
	for further information about available roles and their meanings.

	You may not change your own role.
	
	Parameter *id*:
	  The parameter *id* identifies the topology by giving its unique id.

	Parameter *user*:
	  The name of the user.

	Parameter *role*:
	  The name of the role for this user. If the user already has a role,
	  if will be changed.
	"""
	_getCurrentUserInfo().check_may_grant_permission_for_topologies(_get_topology_info(id))
	top = _getTopology(id)
	user = _getAccount(user)
	top.setRole(user, role)
	
def topology_usage(id): #@ReservedAssignment
	"""
	Retrieves aggregated usage statistics for a topology.
	
	Parameter *id*:
	  The parameter *id* identifies the topology by giving its unique id.

	Return value:
	  Usage statistics for the given topology according to 
	  :doc:`/docs/accountingdata`.
	"""
	_getCurrentUserInfo().check_may_view_topology_usage(_get_topology_info(id))
	top = _getTopology(id)
	return top.totalUsage.info()	


#fixme: move actual import/export to the topology module
#fixme: add authorization checks
def topology_import(data):
	# this function may change the values of data.
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	UserError.check('file_information' in data, code=UserError.INVALID_VALUE, message="Data lacks field file_information")
	info = data['file_information']
	UserError.check('version' in info, code=UserError.INVALID_VALUE, message="File information lacks field version")
	version = info['version']
	
	if version == 3:
		UserError.check('topology' in data, code=UserError.INVALID_VALUE, message="Data lacks field topology")
		return _topology_import_v3(data["topology"])
	elif version == 4:
		UserError.check('topology' in data, code=UserError.INVALID_VALUE, message="Data lacks field topology")
		return _topology_import_v4(data['topology'])
	else:
		raise UserError(code=UserError.INVALID_VALUE, message="Unsuported topology version", data={"version": version})

def _topology_import_v3(top):
	# changes in data model from 3 to 4:
	# everything which was in the 'attrs' subdict is now directly in the root.
	# this is for the topology, all elements, and all connections.
	# thus, v3 topology data can easily be transformed to v4 data, and then the v4 data can be imported:

	for key, value in top['attrs'].iteritems():
		top[key] = value
	del top['attrs']
	for el in top['elements']:
		for key, value in el['attrs'].iteritems():
			el[key] = value
		del el['attrs']
	for conn in top['connections']:
		for key, value in conn['attrs'].iteritems():
			conn[key] = value
		del conn['attrs']

	return _topology_import_v4(top)

def _topology_import_v4(top):
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	top_id = None
	elementIds = {}   
	connectionIds = {}
	errors = [] 
	try:
		# step 0: create new topology
		top_id = topology_create()['id']

		# step 1: apply all topology attributes
		attributes = {key: value for key, value in top.iteritems() if key != "elements" and key != "connections"}
		try:
			topology_modify(top_id, attributes)
		except:
			for key, value in attributes.iteritems():
				try:
					topology_modify(top_id, {key: value})
				except Exception, ex:
					errors.append(("topology", None, key, value, str(ex)))

		# step 2: create elements
		elements = [e for e in top["elements"]]
		maxRepeats = len(elements) * len(elements)  # assume: one element added per round. takes less than n^2 steps
		while len(elements) > 0 and maxRepeats > 0:
			maxRepeats -= 1
			el = elements.pop(0)
			if el['parent'] is None or el['parent'] in elementIds:  # the parent of this element exists (or there is no parent needed)

				parentId = elementIds.get(el.get('parent'))
				elId = element_create(top_id, el['type'], parent=parentId)['id']
				elementIds[el['id']] = elId
				attributes = {key: value for key, value in el.iteritems() if key != "parent" and key != "id" and key != "type"}
				try:
					element_modify(elId, attributes)
				except:
					for key, value in attributes.iteritems():
						try:
							element_modify(elId, {key: value})
						except Exception, ex:
							errors.append(("element", el['id'], key, value, str(ex)))

			else:  # append at the end of the list if parent isn't there yet
				elements.append(el)
		if len(elements) > 0:  # there are elements left where the parent has never been created
			for el in elements:
				errors.append(("element", el['id'], 'parent', el['parent'], "parent cannot be created."))

		for con in top["connections"]:
			el1 = elementIds.get(con["elements"][0])
			el2 = elementIds.get(con["elements"][1])
			conId = connection_create(el1, el2)['id']
			connectionIds[con['id']] = conId
			attributes = {key: value for key, value in con.iteritems() if key != "elements" and key != "id"}
			try:
				connection_modify(conId, attributes)
			except:
				for key, value in attributes.iteritems():
					try:
						connection_modify(conId, {key: value})
					except Exception, ex:
						errors.append(("connection", con['id'], key, value, str(ex)))
	except:
		topology_remove(top_id)
		raise
	return (top_id, elementIds.items(), connectionIds.items(), errors)
	

def topology_export(id): #@ReservedAssignment
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
					 'host_fileserver_port', 'capture_pid', 'topology', 'state', 'vncpassword', 
					 'host_info', 'custom_template', 'timeout',
					 'ipspy_pid', 'last_sync',
					 'rextfv_supported', 'rextfv_status', 'rextfv_max_size', 'info_last_sync',
					 'diskspace', 'ram', 'cpus', 'restricted', 'state_max',
						'_debug_mode', '_initialized']
		blacklist_elements = ['children', 'connection']
		blacklist_connections = ['type']
		data = reduceData_rec(data, blacklist)
		data['elements'] = reduceData_rec(data['elements'], blacklist_elements)
		data['connections'] = reduceData_rec(data['connections'], blacklist_connections)
		return data
	
	UserError.check(currentUser(), code=UserError.NOT_LOGGED_IN, message="Unauthorized")
	top_full = topology_info(id, True)
	top = reduceData(top_full)
	return {'file_information': {'version': 4}, 'topology': top}
		
from host import _getOrganization
from account import _getAccount
from .. import topology, currentUser
from elements import element_create, element_modify 
from connections import connection_create, connection_modify
from ..lib.error import UserError
from ..auth import getAllUsers