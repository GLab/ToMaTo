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
	"""
	This function returns the capability list of either the given host or all hosts which include the provided element type in their capabilities
	:param type: the type of the element ("openvz","kvm","repy") which the host should support
	:param host: the name of a certain host. If left 'None', all hosts will be looked at
	:return: list of capabilities information
	"""
	typeClass = elements.TYPES.get(type)
	UserError.check(typeClass, code=UserError.UNSUPPORTED_TYPE, message="No such element type", data={"type": type})
	if host:
		host = Host.get(name=host)
		UserError.check(host, code=UserError.ENTITY_DOES_NOT_EXIST, message="No such host", data={"host": host})
	return typeClass.getCapabilities()#host)  # fixme: was with param before, but this returned global values anyway

def capabilities_connection(type, host=None): #@ReservedAssignment
	"""
	This function returns the capability list of either the given host or all hosts which include the provided connection type in their capabilities
	:param type: the type of the connection ("bridge","fixed_bridge") which the host should support
	:param host: the name of a certain host. If left 'None', all hosts will be looked at
	:return: list of capabilities information
	"""
	UserError.check(type in ["bridge", "fixed_bridge"], code=UserError.UNSUPPORTED_TYPE, message="No such connection type", data={"type": type})
	if host:
		host = Host.get(name=host)
		UserError.check(host, code=UserError.ENTITY_DOES_NOT_EXIST, message="No such host", data={"host": host})
	return connections.Connection.getCapabilities(type)#, host)  # fixme: was with param before, but this returned global values anyway

@cached(timeout=24*3600, autoupdate=True)
def capabilities():
	"""
	:return: an array with ["element"] and ["connection"] as elements which in turn contain all respective capabilities of all hosts
	"""
	res = {"element": {}, "connection": {}}
	for t in elements.TYPES:
		typeClass = elements.TYPES.get(t)
		res["element"][t] = typeClass.getCapabilities()
	for t in ["bridge", "fixed_bridge"]:
		res["connection"][t] = connections.Connection.getCapabilities(t)
	return res


from .. import elements, connections
from ..host import Host, select
from ..lib.error import UserError
