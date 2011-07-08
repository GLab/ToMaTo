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

def host_info(hostname, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns details about a host. If the host does not exist False is returned.
	
	Parameters:
		string hostname: the name of the host
		  
	Returns: a dict of host details if host exists or False otherwise
	"""
	try:
		return hosts.get(hostname).toDict()
	except hosts.Host.DoesNotExist: # pylint: disable-msg=E1101
		return False

def host_list(group_filter=None, user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns details about all hosts as a list. If group filter is "" all hosts
	will be returned otherwise only the hosts within the group (exact match) .
	
	Parameters:
		string group_filter: host filter by group
		
	Returns: a list of dicts describing all matching hosts 
	"""
	res=[]
	qs = hosts.Host.objects.all() # pylint: disable-msg=E1101
	if group_filter:
		qs=qs.filter(group=group_filter)
	for h in qs:
		res.append(h.toDict())
	return res

def host_add(host_name, group_name, enabled, attrs, user=None):
	"""
	Adds a host to the list of available hosts. First host will be checked,
	then all templates will be uploaded and then finally the host will be 
	available. The result of this method is a task id that can be used to
	observe the check and upload progress. This operation needs admin access.
	
	Parameters:
		string host_name: the host name
		string group_name: the name of the host group
		boolean enabled: whether the host should be enabled
		dict attrs: dictionary with host attributes

	Host attributes in "attrs":
		int vmid_start: begin of the VM id range for ToMaTo
		int vmid_count: number of the VM ids for ToMaTo
		int port_start: begin of the port range for ToMaTo
		int port_count: number of the ports for ToMaTo
		int bridge_start: begin of the bridge id range for ToMaTo
		int bridge_count: number of the bridge ids for ToMaTo

	Returns: task id of the task
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	return hosts.create(host_name, group_name, enabled, attrs)

def host_change(host_name, group_name, enabled, attrs, user=None):
	"""
	Changes a host. The new values will only apply to new topologies or on state change.
	This operation needs admin access.
	
	Parameters:
		string host_name: the host name
		string group_name: the name of the host group
		boolean enabled: whether the host should be enabled
		dict attrs: dictionary with host attributes

	Host attributes in "attrs":
		int vmid_start: begin of the VM id range for ToMaTo
		int vmid_count: number of the VM ids for ToMaTo
		int port_start: begin of the port range for ToMaTo
		int port_count: number of the ports for ToMaTo
		int bridge_start: begin of the bridge id range for ToMaTo
		int bridge_count: number of the bridge ids for ToMaTo

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	hosts.change(host_name, group_name, enabled, attrs)

def host_remove(host_name, user=None):
	"""
	Deletes a host so that the host and all elements depending on it are 
	removed from the database. This will not remove or stop topologies from
	the host. This operation needs admin access.

	Parameters:	
		string host_name: the host name
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	hosts.remove(host_name)

def host_debug(host_name, user=None):
	"""
	Returns debug information about the host. This operation needs admin access.
	
	Parameters:
		string host_name: the host name

	Returns: Debug information

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	return host.debugInfo()

def host_check(host_name, user=None):
	"""
	Performs a sanity check on the host. This method will return a task id that
	can be used to obtain the results. This operation needs admin access.
	
	Parameters:
		string host_name: the host name
	
	Returns: task id
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	return host.check()

def host_groups(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns a list of all host groups.
	
	Returns: list of all host group names
	"""
	return hosts.getGroups()

# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _admin_access
from tomato import hosts