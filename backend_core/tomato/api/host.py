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

from api_helpers import checkauth, _getCurrentUserInfo
from ..lib.cache import cached, invalidates #@UnresolvedImport
from ..lib.service import get_tomato_inner_proxy as _get_tomato_inner_proxy
from ..lib.settings import Config as _Config

#fixme: function won't be accessible after migration
def _getOrganization(name):
	o = Organization.get(name)
	UserError.check(o, code=UserError.ENTITY_DOES_NOT_EXIST, message="Organization with that name does not exist", data={"name": name})
	return o

def _getSite(name):
	s = Site.get(name)
	UserError.check(s, code=UserError.ENTITY_DOES_NOT_EXIST, message="Site with that name does not exist", data={"name": name})
	return s

def _getHost(name):
	h = Host.get(name=name)
	UserError.check(h, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host with that name does not exist", data={"name": name})
	return h

@cached(timeout=6*3600, autoupdate=True)
def organization_list():
	"""
	undocumented
	"""
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	return api.organization_list()

@checkauth
@invalidates(organization_list)
def organization_create(name, label="", attrs={}):
	"""
	undocumented
	"""
	UserError.check(_getCurrentUserInfo(), code=UserError.NOT_LOGGED_IN, message="unauthenticated")
	UserError.check(_getCurrentUserInfo().may_create_organizations(), code=UserError.DENIED, message="unauthorized")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	return api.organization_create(name, label, attrs)

def organization_info(name):
	"""
	undocumented
	"""
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	return api.organization_info()

@checkauth
@invalidates(organization_list)
def organization_modify(name, attrs):
	"""
	undocumented
	"""
	UserError.check(_getCurrentUserInfo(), code=UserError.NOT_LOGGED_IN, message="unauthenticated")
	UserError.check(_getCurrentUserInfo().may_modify_organization(name), code=UserError.DENIED, message="unauthorized")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	return api.organization_modify(name, attrs)

@checkauth
@invalidates(organization_list)
def organization_remove(name):
	"""
	undocumented
	"""
	UserError.check(_getCurrentUserInfo(), code=UserError.NOT_LOGGED_IN, message="unauthenticated")
	UserError.check(_getCurrentUserInfo().may_delete_organization(name), code=UserError.DENIED, message="unauthorized")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	api.organization_remove(name)

@checkauth
def organization_usage(name): #@ReservedAssignment
	#fixme: won't work when organizations are gone from backend_core
	orga = _getOrganization(name)
	return orga.totalUsage.info()	

@cached(timeout=6*3600, autoupdate=True)
def site_list(organization=None):
	"""
	undocumented
	"""
	if organization:
		organization = _getOrganization(organization)
		sites = Site.objects(organization=organization)
	else:
		sites = Site.objects
	return [s.info() for s in sites]

@checkauth
@invalidates(site_list)
def site_create(name, organization, label="", attrs={}):
	"""
	undocumented
	"""
	s = Site.create(name, organization, label, attrs)
	return s.info()

def site_info(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	return site.info()

@checkauth
@invalidates(site_list)
def site_modify(name, attrs):
	"""
	undocumented
	"""
	site = _getSite(name)
	site.modify(attrs)
	return site.info()

@checkauth
@invalidates(site_list)
def site_remove(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	site.remove()

@cached(timeout=300, maxSize=1000, autoupdate=True)
def host_list(site=None, organization=None):
	"""
	undocumented
	"""
	if site:
		site = Site.get(site)
		hosts = Host.objects(site=site)
	elif organization:
		organization = _getOrganization(organization)
		sites = Site.objects(organization=organization)
		hosts = Host.objects(site__in=sites)
	else:
		hosts = Host.objects
	return [h.info() for h in hosts]

@checkauth
@invalidates(host_list)
def host_create(name, site, attrs=None):
	"""
	undocumented
	"""
	if not attrs: attrs = {}
	site = _getSite(site)
	h = Host.create(name, site, attrs)
	return h.info()

@checkauth
def host_info(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	return h.info()

@checkauth
@invalidates(host_list)
def host_modify(name, attrs):
	"""
	undocumented
	"""
	h = _getHost(name)
	h.modify(attrs)
	return h.info()

@checkauth
@invalidates(host_list)
def host_remove(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	h.remove()

@checkauth
def host_users(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	return h.getUsers()

@checkauth
def host_usage(name): #@ReservedAssignment
	h = _getHost(name)
	return h.totalUsage.info()	

from ..host import Host, Site
from ..host.organization import Organization
from ..lib.error import UserError
