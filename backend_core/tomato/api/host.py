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

from ..lib.cache import cached, invalidates

from ..host import Host, Site
from ..lib.error import UserError
from .site import _getSite

def _getHost(name):
	"""
	:rtype: Host
	"""
	h = Host.get(name=name)
	UserError.check(h, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host with that name does not exist", data={"name": name})
	return h

def _host_list(site=None, organization=None):
	"""
	undocumented
	"""
	if site:
		site = Site.get(site)
		return Host.objects(site=site)
	elif organization:
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

def host_users(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	return h.getUsers()

def host_usage(name): #@ReservedAssignment
	h = _getHost(name)
	return h.totalUsage.info()

