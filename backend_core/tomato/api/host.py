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

from ..lib.cache import cached, invalidates

from ..host import Host, Site
from ..lib.error import UserError

def _getSite(name):
	s = Site.get(name)
	UserError.check(s, code=UserError.ENTITY_DOES_NOT_EXIST, message="Site with that name does not exist", data={"name": name})
	return s

def _getHost(name):
	h = Host.get(name=name)
	UserError.check(h, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host with that name does not exist", data={"name": name})
	return h

@cached(timeout=6*3600, autoupdate=True)
def site_list(organization=None):
	"""
	undocumented
	"""
	if organization:
		sites = Site.objects(organization=organization)
	else:
		sites = Site.objects.all()
	return [s.info() for s in sites]

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

@invalidates(site_list)
def site_modify(name, attrs):
	"""
	undocumented
	"""
	site = _getSite(name)
	site.modify(attrs)
	return site.info()

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
		sites = Site.objects(organization=organization)
		hosts = Host.objects(site__in=sites)
	else:
		hosts = Host.objects.all()
	return [h.info() for h in hosts]

@invalidates(host_list)
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

@invalidates(host_list)
def host_modify(name, attrs):
	"""
	undocumented
	"""
	h = _getHost(name)
	h.modify(attrs)
	return h.info()

@invalidates(host_list)
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

