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

def capabilities_element(type, host=None): #@ReservedAssignment
	typeClass = elements.TYPES.get(type)
	fault.check(typeClass, "No such element type: %s", type)
	if host:
		host = modhost.get(address=host)
		fault.check(host, "No such host: %s", host)
	return typeClass.getCapabilities(host)
	
def capabilities_connection(type, host=None): #@ReservedAssignment
	if host:
		host = modhost.get(address=host)
		fault.check(host, "No such host: %s", host)
	return connections.Connection.getCapabilities(type, host)

def capabilities():
	return {
		"element": dict((t, capabilities_element(t)) for t in elements.TYPES),
		"connection": dict((t, capabilities_connection(t)) for t in ["bridge", "fixed_bridge"])
	}

from .. import fault, elements, connections
from .. import host as modhost