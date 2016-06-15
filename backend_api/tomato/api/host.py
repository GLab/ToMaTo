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

from api_helpers import checkauth, getCurrentUserInfo
from ..lib.service import get_backend_core_proxy
from ..lib.remote_info import get_host_info, get_site_info, get_host_list, HostInfo

def host_list(site=None, organization=None):
	"""
	Returns a list of hosts. Depending on the parameter it either returns:
		Site given: All hosts belonging to this site
		Organization given: All hosts belonging to this organization
		Both given: All hosts belonging to the given site, ignoring organization
	:param site: Site name to filter hosts belonging to this site
	:param organization: Organization name to filter hosts belonging to this organization
	:return: list of hosts
	"""
	return get_host_list(site, organization)

def host_create(name, site, attrs=None):
	"""
	Used to create a host on the given site with the provided name
	:param name: Name of the host
	:param site: Name of the site, the host should be located at
	:param attrs: dict with at least two key, value pairs:
		'rpcurl' like this: 'rpcurl': "ssl+jsonrpc://%s:8003" % host_address
		'address'
	:return: Returns the host info of the newly created host
	"""
	site_info = get_site_info(site)
	getCurrentUserInfo().check_may_create_hosts(site_info)
	return HostInfo.create(name, site_info, attrs)

@checkauth
def host_info(name):
	"""
	Returns the host_info object of the host with the given name
	:param name: name of the host
	:return: host_info object
	"""
	host = get_host_info(name)
	return host.info(update=True)

def host_modify(name, attrs):
	"""
	Modifies the host with the given name and the provided attributes
	:param name: Name of the host
	:param attrs: Attribute list to be changed
	:return: host info object of the modified host
	"""
	host = get_host_info(name)
	getCurrentUserInfo().check_may_modify_host(host)
	return host.modify(attrs)

def host_action(name, action, params=None): #@ReservedAssignment
	"""
	Performs an action on the host.
	:param name: Name of the host on which the action should be performed
	:param action: Action which should be executed
	:param params: Dict which contains parameters for the action
	:return: This method returns the result of the action.
	"""
	if not params: params = {}
	host = get_host_info(name)
	return host.action(action, params)

def host_remove(name):
	"""
	Removes the host with the given name, if the host has no elements
	:param name: Name of the host to be removed
	"""
	host = get_host_info(name)
	getCurrentUserInfo().check_may_delete_host(host)
	host.remove()

def host_users(name):
	"""
	List all user that are connected to an element running on the host
	:param name: Name of the host
	:return: List of users
	"""
	getCurrentUserInfo().check_may_list_host_users(get_host_info(name))
	return get_backend_core_proxy().host_users(name)
