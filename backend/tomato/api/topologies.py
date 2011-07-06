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

def top_info(top_id, user=None):
	"""
	Returns detailed information about a topology. The information will vary
	depending on the access level of the user.
	
	Parameters:
		int top_id: id of the topology

	Returns: information about the topology

	Errors:
		fault.Error: if the topology is not found	  
	""" 
	top = topology.get(top_id)
	return top.toDict(user, True)

def top_list(owner_filter=None, host_filter=None, access_filter=None, user=None):
	"""
	Returns brief information about topologies. The set of topologies that will
	be returned can be filtered by owner, by host (affected by the topology) 
	and by access level of the current user. All filters apply subtractively.
	If a filter has the value "" it is not applied.
	
	Parameters:
		string owner_filter: name of the owner to filter by or ""
		string host_filter: name of the host to filter by or ""
		string access_filter: access level to filter by (either "user" or "manager") or ""

	Returns: a list of brief information about topologies
	""" 
	tops=[]
	all_tops = topology.all()
	if owner_filter:
		from tomato import auth
		owner = auth.getUser(owner_filter)
		fault.check(owner, "Unknown user: %s", owner_filter)
		all_tops = all_tops.filter(owner=owner)
	if host_filter:
		all_tops = all_tops.filter(device__host__name=host_filter).distinct()
	for t in all_tops:
		if (not access_filter) or t.checkAccess(access_filter, user):
			tops.append(t.toDict(user, False))
	return tops
	
def top_create(user=None):
	"""
	Creates a new empty topology to be modified via top_modify afterwards.
	The user must be a regular user to create topologies.
	
	Returns: the id of the new topology
	""" 
	fault.check(user.is_user, "only regular users can create topologies")
	top=topology.create(user)
	top.save()
	top.logger().log("created", user=user.name)
	return top.id

def top_modify(top_id, mods, direct=False, user=None):
	"""
	Applies the list of modifications to the topology. The user must
	have at least manager access to the topology. The result of this method
	is a task id that runs the modifications.
	This method implicitly renews the topology.
	
	Parameters:
		int top_id: the id of the topology
		list of dict mods: the modifications list
		boolean direct: whether to execute the modification directly

	Returns: the id of the modification task (not direct) or None (direct) 
	""" 
	#FIXME: describe all possible modifications
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("modifying topology", user=user.name, bigmessage=str(mods))
	from tomato import modification
	res = modification.modifyList(top, mods, direct)
	if not direct:
		top.logger().log("started task %s" % res, user=user.name)
	return res

def top_action(top_id, action, element_type="topology", element_name=None, attrs={}, direct=False, user=None):
	"""
	Executes the given action on a topology element. The minimum user access
	level depends on the action.
	
	Parameters:
		int top_id: the id of the topology
		string action: the action to perform
		string element_type: the type of the element (topology, device or connector)
		string element_name: the name of the element
		dict attrs: attributes for the action
		boolean direct: whether to execute the action directly (non-detached)

	Returns: the id of the action task (not direct) or None (direct) 
	""" 
	#FIXME: describe all possible actions
	top = topology.get(top_id)
	_top_access(top, "user", user)
	if element_type == "topology":
		element = top
	elif element_type == "device":
		element = top.deviceSetGet(element_name)
	elif element_type == "connector":
		element = top.connectorSetGet(element_name)
	else:
		fault.check(False, "Unknown element type: %s", element_type)
	top.logger().log("%s %s %s" % (action, element_type, element_name), user=user.name)
	return element.action(user, action, attrs, direct)
	
def permission_set(top_id, user_name, role, user=None):
	"""
	Adds a permission entry to a topology. Acceptable roles are "user" and
	"manager". This method requires owner access to the topology.

	Parameters:
		int top_id: id of the topology
		string user_name: user name
		string role: role of the permission (either "user" or "manager")
	"""
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	if user_name != top.owner:
		top.permissionsRemove(user_name)
	if role:
		top.permissionsAdd(user_name, role)
	top.logger().log("set permission: %s=%s" % (user_name, role))
	
# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _top_access
from tomato import topology, fault