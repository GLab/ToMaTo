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

from ..lib.cache import cached #@UnresolvedImport

def capabilities_element(type, host=None): #@ReservedAssignment
	typeClass = elements.TYPES.get(type)
	UserError.check(typeClass, code=UserError.UNSUPPORTED_TYPE, message="No such element type", data={"type": type})
	if host:
		host = modhost.get(name=host)
		UserError.check(host, code=UserError.ENTITY_DOES_NOT_EXIST, message="No such host", data={"host": host})
	return typeClass.getCapabilities(host)
	
def capabilities_connection(type, host=None): #@ReservedAssignment
	if host:
		host = modhost.get(name=host)
		UserError.check(host, code=UserError.ENTITY_DOES_NOT_EXIST, message="No such host", data={"host": host})
	return connections.Connection.getCapabilities(type, host)

@cached(timeout=24*3600)
def capabilities():
	return {
		"element": dict((t, capabilities_element(t)) for t in elements.TYPES),
		"connection": dict((t, capabilities_connection(t)) for t in ["bridge", "fixed_bridge"])
	}

from .. import elements, connections
from .. import host as modhost
from ..lib.error import UserError
