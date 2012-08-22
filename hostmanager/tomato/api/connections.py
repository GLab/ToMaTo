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

def _getConnection(id_):
    con = connections.get(id_, owner=currentUser())
    fault.check(con, "No such connection: id=%d" % id_)
    return con

def connection_create(element1, element2, type=None, attrs={}): #@ReservedAssignment
    """
    Connects the given elements using the given type of connection, configuring
    it with the given attributes by the way. The order of the elements does not
    matter. The given connection type must support the element types.
    
    @param element1: The id of the first element to connect
    @type element1: int

    @param element2: The id of the second element to connect
    @type element2: int

    @param type: The type of the connection, must either be one of the 
        supported connections types or None to determine automatically.
    @type type: str
     
    @param attrs: Attributes to configure the connection with. The allowed
        attributes and their meanings depend on the connection type.
    @type attrs: dict
    
    @return: Information about the connection
    @rtype: dict    
    
    @raise various other errors: depending on the type
    """
    el1 = _getElement(element1)
    el2 = _getElement(element2)
    con = connections.create(el1, el2, type, attrs)
    return con.info()

def connection_modify(id, attrs): #@ReservedAssignment
    """
    Modifies a connection, configuring it with the given attributes.
    
    @param id: The id of the connection
    @type id: int
     
    @param attrs: Attributes to configure the connection with. The allowed
        attributes and their meanings depend on the connection type.
    @type attrs: dict
    
    @return: Information about the connection
    @rtype: dict    
    
    @raise No such connection: if the connection id does not exist or belongs
        to another owner
    @raise various other errors: depending on the type
    """
    con = _getConnection(int(id))
    con.modify(attrs)
    return con.info()

def connection_action(id, action, params={}): #@ReservedAssignment
    """
    Performs an action on the connection.
    
    @param id: The id of the connection
    @type id: int
     
    @param action: The action to be performed on the connection. The allowed
        actions and their meanings depend on the connection type.
    @type action: str

    @param params: Parameters for the action. The parameters and their meanings
        depend on the connection type.
    @type params: dict
    
    @return: Return value of the action
    
    @raise No such connection: if the connection id does not exist or belongs
        to another owner
    @raise various other errors: depending on the type
    """
    con = _getConnection(int(id))
    res = con.action(action, params)
    return {} if res is None else res 

def connection_remove(id): #@ReservedAssignment
    """
    Removes a conection.
    
    @param id: The id of the connection
    @type id: int
     
    @return: {}
    @rtype: dict    
    
    @raise No such connection: if the connection id does not exist or belongs
        to another owner
    @raise various other errors: depending on the type
    """
    con = _getConnection(int(id))
    con.remove()
    return {}

def connection_info(id): #@ReservedAssignment
    """
    Retrieves information about a connection.
    
    @param id: The id of the connection
    @type id: int
     
    @return: Information about the connection
    @rtype: dict    
    
    @raise No such connection: if the connection id does not exist or belongs
        to another owner
    """
    con = _getConnection(int(id))
    return con.info()
    
def connection_list():
    """
    Retrieves information about all connections of the user. 
    
    @return: Information about the connections
    @rtype: list of dicts    
    """
    return [con.info() for con in connections.getAll(owner=currentUser())]

from tomato import fault, connections, currentUser
from elements import _getElement