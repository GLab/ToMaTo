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

from tomato.lib.decorators import xmlRpcSanitize #@UnresolvedImport

def host_info():
    """
    Retrieves general information about the host. 
    
    @return: general Information about the host
    @rtype: dict    
    """
    return {
        "hostmanager": {
            "version": config.VERSION,
        },
        "fileserver_port": config.FILESERVER["port"],
        "address": config.PUBLIC_ADDRESS,
        "resources": {
            "cpus_present": hostinfo.cpuinfo(),
            "memory": hostinfo.meminfo(),
            "loadavg": hostinfo.loadavg(),
            "diskspace": {
                "root": hostinfo.diskinfo("/"),
                "data": hostinfo.diskinfo(config.DATA_DIR),
            },
        },
        "uptime": hostinfo.uptime(),
        "time": time.time(),
    }

@xmlRpcSanitize
def host_capabilities():
    """
    Retrieves the capabilities of the host. 
    
    @return: Information about the host capabilities
    @rtype: dict
    """
    element_types = {}
    for type_, class_ in tomato.elements.TYPES.iteritems():
        caps = {}
        for cap in ["actions", "next_state", "children", "parent", "con_concepts"]:
            caps[cap] = getattr(class_, "CAP_"+cap.upper())
        caps["attrs"] = class_.cap_attrs()
        element_types[type_] = caps
    connection_types = {}
    for type_, class_ in tomato.connections.TYPES.iteritems():
        caps = {}
        for cap in ["actions", "next_state", "con_concepts"]:
            caps[cap] = getattr(class_, "CAP_"+cap.upper())
        caps["attrs"] = class_.cap_attrs()
        connection_types[type_] = caps
    return {
        "elements": element_types,
        "connections": connection_types,
        "resources": dict([(type_, {}) for type_ in tomato.resources.TYPES]),
    }

import tomato.elements
import tomato.resources
from tomato import config
from tomato.lib.cmd import hostinfo #@UnresolvedImport
import time