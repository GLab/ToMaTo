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

def accounting_statistics():
    elSt = dict([(str(el.id), el.usageStatistics.info()) for el in elements.getAll(owner=currentUser())])
    conSt = dict([(str(con.id), con.usageStatistics.info()) for con in connections.getAll(owner=currentUser())])
    return {"elements": elSt, "connections": conSt}

def accounting_element_statistics(id): #@ReservedAssignment
    return _getElement(id).usageStatistics.info()
    
def accounting_connection_statistics(id): #@ReservedAssignment
    return _getConnection(id).usageStatistics.info()

from elements import _getElement
from connections import _getConnection
from tomato import currentUser, elements, connections
