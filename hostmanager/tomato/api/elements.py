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

def _getElement(id_):
    el = elements.get(id_, owner=currentUser())
    fault.check(el, "No such element: id=%d", id_)
    return el

def element_create(type, parent=None, attrs={}): #@ReservedAssignment
    """
    Creates an element of given type and with the given parent element, 
    configuring it with the given attributes by the way.
    
    @param type: The type of the new element, must be one of the supported
        element types.
    @type type: str
     
    @param parent: The id of the parent element or None for no parent element.
        Element types might restrict type and number of their children elements
        or the type of their parent element.
    @type parent: int  
    
    @param attrs: Attributes to configure the new element with. The allowed
        attributes and their meanings depend on the element type.
    @type attrs: dict
    
    @return: Information about the element
    @rtype: dict    
    
    @raise No such element: if the parent element id does not exist or belongs
        to another owner
    @raise various other errors: depending on the type
    """
    parentEl = _getElement(int(parent)) if parent else None
    attrs = dict(attrs)
    el = elements.create(type, parentEl, attrs)
    return el.info()

def element_modify(id, attrs): #@ReservedAssignment
    """
    Modifies an element, configuring it with the given attributes.
    
    @param id: The id of the element
    @type id: int
     
    @param attrs: Attributes to configure the element with. The allowed
        attributes and their meanings depend on the element type.
    @type attrs: dict
    
    @return: Information about the element
    @rtype: dict    
    
    @raise No such element: if the element id does not exist or belongs to
        another owner
    @raise various other errors: depending on the type
    """
    el = _getElement(int(id))
    el.modify(attrs)
    return el.info()

def element_action(id, action, params={}): #@ReservedAssignment
    """
    Performs an action on the element and possibly on its children too.
    
    @param id: The id of the element
    @type id: int
     
    @param action: The action to be performed on the element. The allowed
        actions and their meanings depend on the element type.
    @type action: str

    @param params: Parameters for the action. The parameters and their meanings
        depend on the element type.
    @type params: dict
    
    @return: Return value of the action
    
    @raise No such element: if the element id does not exist or belongs to
        another owner
    @raise various other errors: depending on the type
    """
    el = _getElement(int(id))
    res = el.action(action, params)
    return {} if res is None else res 

def element_remove(id, recurse=True): #@ReservedAssignment
    """
    Removes an element and possibly all its children too.
    
    @param id: The id of the element
    @type id: int
     
    @param recurse: Whether to remove all children first or simply fail if 
        children exist. 
    @type recurse: bool

    @return: {}
    @rtype: dict    
    
    @raise No such element: if the element id does not exist or belongs to
        another owner
    @raise various other errors: depending on the type
    """
    el = _getElement(int(id))
    el.remove(recurse)
    return {}

def element_info(id): #@ReservedAssignment
    """
    Retrieves information about an element.
    
    @param id: The id of the element
    @type id: int
     
    @return: Information about the element
    @rtype: dict    
    
    @raise No such element: if the element id does not exist or belongs to
        another owner
    """
    el = _getElement(int(id))
    return el.info()
    
def element_list(type_filter=None):
    """
    Retrieves information about all elements of the user. 
     
    @param type_filter: If set, the method only returns elements with the given
        type.
    @type type_filter: str
     
    @return: Information about the elements
    @rtype: list of dicts    
    """
    els = elements.getAll(owner=currentUser(), type=type_filter) if type_filter else elements.getAll(owner=currentUser())
    return [el.info() for el in els]

from tomato import fault, elements, currentUser