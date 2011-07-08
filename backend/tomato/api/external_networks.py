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
	
def external_network_add(type, group, params, user=None):
	"""
	Adds an external network. This operation needs admin access.
	
	Parameters:
		string type: type of the external network
		string group: group of the external network
		dict params: dict of all additional parameters

	Additional parameters in "params":
		int max_devices: maximal allowed connections to this external network
		bool avoid_duplicates: whether to make sure that connections to the 
			same external network in a topology will be using different bridges

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	if not params.has_key("max_devices"):
		params["max_devices"] = None
	if not params.has_key("avoid_duplicates"):
		params["avoid_duplicates"] = False
	hosts.ExternalNetwork.objects.create(type=type, group=group, max_devices=params["max_devices"], avoid_duplicates=params["avoid_duplicates"])

def external_network_change(type, group, params, user=None):
	"""
	Changes an external network. This operation needs admin access.

	Parameters:	
		string type: type of the external network
		string group: name of the external network
		dict params: dict of all additional parameters

	Additional parameters in "params":
		int max_devices: maximal allowed connections to this external network
		bool avoid_duplicates: whether to make sure that connections to the 
			same external network in a topology will be using different bridges

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	en = hosts.ExternalNetwork.objects.get(type=type, group=group)
	if not params.has_key("max_devices"):
		params["max_devices"] = None
	if not params.has_key("avoid_duplicates"):
		params["avoid_duplicates"] = False
	en.max_devices = params["max_devices"]
	en.avoid_duplicates = params["avoid_duplicates"]
	en.save()

def external_network_remove(type, group, user=None):
	"""
	Removes an external network. This operation needs admin access.
	
	Parameters:
		string type: type of the external network
		string group: name of the external network
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	en = hosts.ExternalNetwork.objects.get(type=type, group=group)
	fault.check(not len(en.externalnetworkbridge_set.all()), "External network still has bridges: %s", en)
	en.delete()

def external_network_bridge_add(host_name, type, group, bridge, user=None):
	"""
	Adds an external network bridge to a host. This operation needs admin access.
	
	Parameters:
		string host_name: name of the host
		string type: type of the external network
		string group: group of the external network
		string bridge: bridge to connect interfaces to
	
	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	host.externalNetworksAdd(type, group, bridge)

def external_network_bridge_remove(host_name, type, group, user=None):
	"""
	Removes an external network bridge to a host. This operation needs admin access.
	
	Parameters:
		string host_name: name of the host
		string type: type of the external network
		string group: group of the external network

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	_admin_access(user)
	host = hosts.get(host_name)
	host.externalNetworksRemove(type, group)

def external_networks(user=None): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Returns a list of all external networks
	
	Returns: a list of all external networks with all bridges

	Errors:
		fault.Error: if the user does not have enough privileges  
	"""
	return hosts.external_networks.getAll()

# keep internal imports at the bottom to avoid dependency problems
from tomato.api import _admin_access
from tomato import hosts, fault