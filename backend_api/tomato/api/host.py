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

#fixme: all.

from api_helpers import checkauth, getCurrentUserInfo
from ..lib.service import get_backend_users_proxy, get_backend_core_proxy
from ..lib.remote_info import get_host_info, get_site_info

def organization_list():
	"""
	undocumented
	"""
	api = get_backend_users_proxy()
	return api.organization_list()

def organization_create(name, label="", attrs={}):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_organizations()
	api = get_backend_users_proxy()
	return api.organization_create(name, label, attrs)

def organization_info(name):
	"""
	undocumented
	"""
	api = get_backend_users_proxy()
	return api.organization_info(name)

def organization_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_organization(name)
	api = get_backend_users_proxy()
	return api.organization_modify(name, attrs)

def organization_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_organization(name)
	api = get_backend_users_proxy()
	api.organization_remove(name)

@checkauth
def organization_usage(name): #@ReservedAssignment
	#fixme: broken
	orga = _getOrganization(name)
	return orga.totalUsage.info()	

def site_list(organization=None):
	"""
	undocumented
	"""
	return get_backend_core_proxy().site_list(organization)

def site_create(name, organization, label="", attrs={}):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_sites(organization)
	return get_backend_core_proxy().site_create(name, organization, label, attrs)

def site_info(name):
	"""
	undocumented
	"""
	return get_backend_core_proxy().site_info(name)

def site_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_site(get_site_info(name))
	return get_backend_core_proxy().site_modify(name, attrs)

def site_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_site(get_site_info(name))
	return get_backend_core_proxy().site_remove(name)

def host_list(site=None, organization=None):
	"""
	undocumented
	"""
	return get_backend_core_proxy().host_list(site, organization)

def host_create(name, site, attrs=None):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_hosts(get_site_info(site))
	return get_backend_core_proxy().host_create(name, site, attrs)

@checkauth
def host_info(name):
	"""
	undocumented
	"""
	return get_backend_core_proxy().host_info(name)

def host_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_host(get_host_info(name))
	return get_backend_core_proxy().host_modify(name, attrs)

def host_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_host(get_host_info(name))
	get_backend_core_proxy().host_remove(name)

def host_users(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_list_host_users(get_host_info(name))
	return get_backend_core_proxy().host_users(name)

@checkauth
def host_usage(name): #@ReservedAssignment
	return get_backend_core_proxy().host_usage(name)

