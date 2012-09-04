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

def _getResource(id_):
    res = resources.get(id_)
    fault.check(res, "No such resource: id=%d", id_, code=fault.UNKNOWN_OBJECT)
    return res

def resource_create(type, attrs={}): #@ReservedAssignment
    """
    Creates a resource of given type configuring it with the given attributes
    by the way.
    
    @param type: The type of the new resource.
    @type type: str
     
    @param attrs: Attributes to configure the new resource with. The allowed
        attributes and their meanings depend on the resource type.
    @type attrs: dict
    
    @return: Information about the resource
    @rtype: dict    
    
    @raise various other errors: depending on the type
    """
    attrs = dict(attrs)
    res = resources.create(type, attrs)
    return res.info()

def resource_modify(id, attrs): #@ReservedAssignment
    """
    Modifies a resource, configuring it with the given attributes.
    
    @param id: The id of the resource
    @type id: int
     
    @param attrs: Attributes to configure the resource with. The allowed
        attributes and their meanings depend on the resource type.
    @type attrs: dict
    
    @return: Information about the resource
    @rtype: dict    
    
    @raise No such resource: if the resource id does not exist or belongs to
        another owner
    @raise various other errors: depending on the type
    """
    res = _getResource(int(id))
    res.modify(attrs)
    return res.info()

def resource_remove(id): #@ReservedAssignment
    """
    Removes a resource.
    
    @param id: The id of the resource
    @type id: int
     
    @return: {}
    @rtype: dict    
    
    @raise No such resource: if the resource id does not exist
    @raise various other errors: depending on the type
    """
    res = _getResource(int(id))
    res.remove()
    return {}

def resource_info(id): #@ReservedAssignment
    """
    Retrieves information about a resource.
    
    @param id: The id of the resource
    @type id: int
     
    @return: Information about the resource
    @rtype: dict    
    
    @raise No such resource: if the resource id does not exist
    """
    res = _getResource(int(id))
    return res.info()
    
def resource_list(type_filter=None):
    """
    Retrieves information about all resources. 
    
    @param type_filter: If this is set, only resources of matching type will be
        returned.
    @type type_filter: str

    @return: Information about the resources
    @rtype: list of dicts    
    """
    res = resources.getAll(type=type_filter) if type_filter else resources.getAll()
    return [r.info() for r in res]

from tomato import fault, resources