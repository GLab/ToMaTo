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

from api_helpers import checkauth
from ..lib.cache import cached, invalidates #@UnresolvedImport

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
	return [o.info() for o in Organization.objects.all()]

@checkauth
@invalidates(organization_list)
def organization_create(name, label="", attrs={}):
	"""
	undocumented
	"""
	o = Organization.create(name, label, attrs)
	return o.info()

def organization_info(name):
	"""
	undocumented
	"""
	orga = _getOrganization(name)
	return orga.info()

@checkauth
@invalidates(organization_list)
def organization_modify(name, attrs):
	"""
	undocumented
	"""
	orga = _getOrganization(name)
	orga.modify(attrs)
	return orga.info()

@checkauth
@invalidates(organization_list)
def organization_remove(name):
	"""
	undocumented
	"""
	orga = _getOrganization(name)
	orga.remove()

@checkauth
def organization_usage(name): #@ReservedAssignment
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
		hosts = Host.objects(site__name=site)
	elif organization:
		hosts = Host.objects(site__organization__name=organization)
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
