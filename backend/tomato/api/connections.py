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

from tomato import fault, connections, currentUser #@UnusedImport
from elements import _getElement

def _getConnection(id_):
    con = connections.get(id_)
    fault.check(con, "Connection with id #%d does not exist", id_)
    return con

def connection_create(el1, el2, attrs={}): #@ReservedAssignment
    el1 = _getElement(el1)
    el2 = _getElement(el2)
    con = connections.create(el1, el2, attrs)
    return con.info()

def connection_modify(id, attrs): #@ReservedAssignment
    con = _getConnection(id)
    con.modify(attrs)
    return con.info()

def connection_action(id, action, params={}): #@ReservedAssignment
    con = _getConnection(id)
    return con.action(action, params)

def connection_remove(id): #@ReservedAssignment
    con = _getConnection(id)
    con.remove()

def connection_info(id): #@ReservedAssignment
    con = _getConnection(id)
    return con.info()
    
