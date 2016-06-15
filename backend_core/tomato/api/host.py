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

from ..host import Host, Site
from ..lib.error import UserError
from .site import _getSite
from ..lib.remote_info import get_organization_info

def _getHost(name):
	"""
	:rtype: Host
	"""
	h = Host.get(name=name)
	UserError.check(h, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host with that name does not exist", data={"name": name})
	return h

def _host_list(site=None, organization=None):
	"""
	Returns a list of hosts. Depending on the parameter it either returns:
		Site given: All hosts belonging to this site
		Organization given: All hosts belonging to this organization
		Both given: All hosts belonging to the given site, ignoring organization
	:param site: Site name to filter hosts belonging to this site
	:param organization: Organization name to filter hosts belonging to this organization
	:return: list of hosts
	"""
	if site:
		UserError.check(Site.get(site) is not None, code=UserError.ENTITY_DOES_NOT_EXIST, message="Site with that name does not exist")
		site = Site.get(site)
		return Host.objects(site=site)
	elif organization:
		UserError.check(get_organization_info(organization).exists(), code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist")
		sites = Site.objects(organization=organization)
		return Host.objects(site__in=sites)
	else:
		return Host.objects.all()

def host_list(site=None, organization=None):
	"""
	return a list of hosts
	:rtype: list(str)
	"""
	return [h.info() for h in _host_list(site, organization)]

def host_name_list(site=None, organization=None):
	"""
	return a list of hosts, but only their names
	:rtype: list(str)
	"""
	return [h.name for h in _host_list(site, organization)]

def host_dump_list(name, after):
	"""
	return all dumps of this host since last_updatetime
	"""
	return _getHost(name).getProxy().dump_list(after)

def host_create(name, site, attrs=None):
	"""
	undocumented
	"""
	if not attrs: attrs = {}
	site = _getSite(site)
	h = Host.create(name, site, attrs)
	return h.info()

def host_info(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	return h.info()

def host_modify(name, attrs):
	"""
	undocumented
	"""
	h = _getHost(name)
	h.modify(attrs)
	return h.info()

def host_remove(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	h.remove()

def host_action(name, action, params=None): #@ReservedAssignment
	"""
	undocumented
	"""
	if not params: params = {}
	host = _getHost(name)
	return host.action(action, params)

def host_users(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	return h.getUsers()

def host_execute_function(name, function_name, *args, **kwargs):
	return getattr(_getHost(name).getProxy(), function_name)(*args, **kwargs)
