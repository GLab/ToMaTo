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

def server_info():
    return {
        "TEMPLATE_TRACKER_URL": "http://%s:%d/announce" % (config.PUBLIC_ADDRESS, config.TRACKER_PORT),
    }

def _getSite(name):
    s = host.getSite(name)
    fault.check(s, "Site with name %s does not exist", name)
    return s

def _getHost(address):
    h = host.get(address=address)
    fault.check(h, "Host with address %s does not exist", address)
    return h

def site_create(name, description=""):
    s = host.createSite(name, description)
    return s.info()

def site_list():
    return [s.info() for s in host.getAllSites()]

def site_remove(name):
    site = _getSite(name)
    host.removeSite(site)

def host_create(address, site, attrs={}):
    site = _getSite(site)
    h = host.create(address, site, attrs)
    return h.info()

def host_list(site_filter=None):
    hosts = host.getAll(site__name=site_filter) if site_filter else host.getAll()
    return [h.info() for h in hosts]

def host_remove(address):
    h = _getHost(address)
    host.remove(h)

def host_element_owner(hostname, num):
    h = _getHost(hostname)
    try:
        hel = h.getElement(num)
    except host.HostElement.DoesNotExist:
        fault.raise_("Host element %d on host %s is not used" % (num, hostname), fault.USER_ERROR)
    return hel.getOwner()

def host_connection_owner(hostname, num):
    h = _getHost(hostname)
    try:
        hcon = h.getConnection(num)
    except host.HostConnection.DoesNotExist:
        fault.raise_("Host connection %d on host %s is not used" % (num, hostname), fault.USER_ERROR)
    return hcon.getOwner()

from tomato import host, fault, config