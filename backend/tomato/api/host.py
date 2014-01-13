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

def organization_create(name, description=""):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	o = host.createOrganization(name, description)
	return o.info()

def organization_info(name):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	orga = _getOrganization(name)
	return orga.info()

def organization_list():
	"""
	undocumented
	"""
	return [o.info() for o in host.getAllOrganizations()]

def organization_modify(name, attrs):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	orga = _getOrganization(name)
	orga.modify(attrs)
	return orga.info()

def organization_remove(name):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	orga = _getOrganization(name)
	orga.remove()

def site_create(name, organization, description=""):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	s = host.createSite(name, organization, description)
	return s.info()

def site_info(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	return site.info()

def site_list():
	"""
	undocumented
	"""
	return [s.info() for s in host.getAllSites()]

def site_modify(name, attrs):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	site = _getSite(name)
	site.modify(attrs)
	return site.info()

def site_remove(name):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	site = _getSite(name)
	site.remove()

def host_create(address, site, attrs={}):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	site = _getSite(site)
	h = host.create(address, site, attrs)
	return h.info()

def host_info(address):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	h = _getHost(address)
	return h.info()

def host_list(site_filter=None):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	hosts = host.getAll(site__name=site_filter) if site_filter else host.getAll()
	return [h.info() for h in hosts]

def host_modify(address, attrs):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	h = _getHost(address)
	h.modify(attrs)
	return h.info()

def host_remove(address):
	"""
	undocumented
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	h = _getHost(address)
	h.remove()

from .. import host, fault, currentUser
from ..lib.rpc import ErrorUnauthorized  #@UnresolvedImport