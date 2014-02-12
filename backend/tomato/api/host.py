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
from ..lib.cache import cached #@UnresolvedImport

def _getOrganization(name):
	o = host.getOrganization(name)
	fault.check(o, "Organization with name %s does not exist", name)
	return o

def _getSite(name):
	s = host.getSite(name)
	fault.check(s, "Site with name %s does not exist", name)
	return s

def _getHost(address):
	h = host.get(address=address)
	fault.check(h, "Host with address %s does not exist", address)
	return h

@cached(timeout=6*3600)
def organization_list():
	"""
	undocumented
	"""
	return [o.info() for o in host.getAllOrganizations()]

@checkauth
def organization_create(name, description=""):
	"""
	undocumented
	"""
	o = host.createOrganization(name, description)
	organization_list.invalidate()
	return o.info()

def organization_info(name):
	"""
	undocumented
	"""
	orga = _getOrganization(name)
	return orga.info()

@checkauth
def organization_modify(name, attrs):
	"""
	undocumented
	"""
	orga = _getOrganization(name)
	orga.modify(attrs)
	organization_list.invalidate()
	return orga.info()

@checkauth
def organization_remove(name):
	"""
	undocumented
	"""
	orga = _getOrganization(name)
	orga.remove()
	organization_list.invalidate()

@cached(timeout=6*3600)
def site_list(organization=None):
	"""
	undocumented
	"""
	if organization:
		organization = _getOrganization(organization)
		sites = host.getAllSites(organization=organization)
	else:
		sites = host.getAllSites()
	return [s.info() for s in sites]

@checkauth
def site_create(name, organization, description=""):
	"""
	undocumented
	"""
	s = host.createSite(name, organization, description)
	site_list.invalidate()
	return s.info()

def site_info(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	return site.info()

@checkauth
def site_modify(name, attrs):
	"""
	undocumented
	"""
	site = _getSite(name)
	site.modify(attrs)
	site_list.invalidate()
	return site.info()

@checkauth
def site_remove(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	site.remove()
	site_list.invalidate()

@cached(timeout=300)
def host_list(site=None, organization=None):
	"""
	undocumented
	"""
	if site:
		hosts = host.getAll(site__name=site)
	elif organization:
		hosts = host.getAll(site__organization__name=organization)
	else:
		hosts = host.getAll()
	return [h.info() for h in hosts]

@checkauth
def host_create(address, site, attrs={}):
	"""
	undocumented
	"""
	site = _getSite(site)
	h = host.create(address, site, attrs)
	host_list.invalidate()
	return h.info()

@checkauth
def host_info(address):
	"""
	undocumented
	"""
	h = _getHost(address)
	return h.info()

@checkauth
def host_modify(address, attrs):
	"""
	undocumented
	"""
	h = _getHost(address)
	h.modify(attrs)
	host_list.invalidate()
	return h.info()

@checkauth
def host_remove(address):
	"""
	undocumented
	"""
	h = _getHost(address)
	h.remove()
	host_list.invalidate()

from .. import host, fault