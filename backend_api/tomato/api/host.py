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
	undocumented
	"""
	return get_host_list(site, organization)

def host_create(name, site, attrs=None):
	"""
	undocumented
	"""
	site_info = get_site_info(site)
	getCurrentUserInfo().check_may_create_hosts(site_info)
	return HostInfo.create(name, site_info, attrs)

@checkauth
def host_info(name):
	"""
	undocumented
	"""
	host = get_host_info(name)
	return host.info(update=True)

def host_modify(name, attrs):
	"""
	undocumented
	"""
	host = get_host_info(name)
	getCurrentUserInfo().check_may_modify_host(host)
	return host.modify(name, attrs)

def host_remove(name):
	"""
	undocumented
	"""
	host = get_host_info(name)
	getCurrentUserInfo().check_may_delete_host(host)
	host.remove(name)

def host_users(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_list_host_users(get_host_info(name))
	return get_backend_core_proxy().host_users(name)

@checkauth
def host_usage(name): #@ReservedAssignment
	return get_backend_core_proxy().host_usage(name)

