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

def _parseDate(date):
    if isinstance(date, xmlrpclib.DateTime):
        date = date.value
    return datetime.datetime.strptime(date, "%Y%m%dT%H:%M:%S")

def accounting_statistics(after=None, before=None):
    after = _parseDate(after) if after else None 
    before = _parseDate(before) if before else None 
    elSt = dict([(str(el.id), el.usageStatistics.info(after, before)) for el in elements.getAll(owner=currentUser())])
    conSt = dict([(str(con.id), con.usageStatistics.info(after, before)) for con in connections.getAll(owner=currentUser())])
    return {"elements": elSt, "connections": conSt}

def accounting_element_statistics(id, after=None, before=None): #@ReservedAssignment
    after = _parseDate(after) if after else None 
    before = _parseDate(before) if before else None 
    return _getElement(id).usageStatistics.info(after, before)
    
def accounting_connection_statistics(id, after=None, before=None): #@ReservedAssignment
    after = _parseDate(after) if after else None 
    before = _parseDate(before) if before else None 
    return _getConnection(id).usageStatistics.info(after, before)

from elements import _getElement
from connections import _getConnection
from tomato import currentUser, elements, connections
import xmlrpclib
import datetime