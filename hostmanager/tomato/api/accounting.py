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

"""
See :doc:`/docs/accountingdata` for documentation of the data type used for
accounting. 
"""

def accounting_statistics(type=None, after=None, before=None): #@ReservedAssignment
    """
    Returns usage statistics for all elements and all connections.
    
    Parameter *type*:
      If this parameter is set, only usage records of the given type are
      returned.
      
    Parameter *after*:
      If this parameter is set, only usage records with a start date after
      the given date will be returned. The date must be given as the number
      of seconds since the epoch (1970-01-01 00:00:00).
      If this parameter is omitted, all usage records from begin of recording
      will be returned.
      
    Parameter *before*:
      If this parameter is set, only usage records with an end date before
      the given date will be returned. The date must be given as the number
      of seconds since the epoch (1970-01-01 00:00:00).
      If this parameter is omitted, all usage records until now will be 
      returned. 
      
    Return value:
      This method returns a dict with the following keys.
      
      ``elements``:
        A dict with usage statistics for all elements. The keys of the dict are
        the element ids (as strings) and the values are the usage statistics.
      
      ``connections``:
        A dict with usage statistics for all connections. The keys of the dict
        are the connection ids (as strings) and the values are the usage 
        statistics.
    """
    elSt = dict([(str(el.id), el.usageStatistics.info(type, after, before)) for el in elements.getAll(owner=currentUser())])
    conSt = dict([(str(con.id), con.usageStatistics.info(type, after, before)) for con in connections.getAll(owner=currentUser())])
    return {"elements": elSt, "connections": conSt}

def accounting_element_statistics(id, type=None, after=None, before=None): #@ReservedAssignment
    """
    Returns accounting statistics for one element.
    
    Parameter *id*:
      The id of the element.
      
    Parameter *type*:
      If this parameter is set, only usage records of the given type are
      returned.
      
    Parameter *after*:
      If this parameter is set, only usage records with a start date after
      the given date will be returned. The date must be given as the number
      of seconds since the epoch (1970-01-01 00:00:00).
      If this parameter is omitted, all usage records from begin of recording
      will be returned.
      
    Parameter *before*:
      If this parameter is set, only usage records with an end date before
      the given date will be returned. The date must be given as the number
      of seconds since the epoch (1970-01-01 00:00:00).
      If this parameter is omitted, all usage records until now will be 
      returned.
      
    Return value:
      This method returns usage statistics for the given element.
    """
    return _getElement(id).usageStatistics.info(type, after, before)
    
def accounting_connection_statistics(id, type=None, after=None, before=None): #@ReservedAssignment
    """
    Returns accounting statistics for one connection.
    
    Parameter *id*:
      The id of the connection.
      
    Parameter *type*:
      If this parameter is set, only usage records of the given type are
      returned.
      
    Parameter *after*:
      If this parameter is set, only usage records with a start date after
      the given date will be returned. The date must be given as the number
      of seconds since the epoch (1970-01-01 00:00:00).
      If this parameter is omitted, all usage records from begin of recording
      will be returned.
      
    Parameter *before*:
      If this parameter is set, only usage records with an end date before
      the given date will be returned. The date must be given as the number
      of seconds since the epoch (1970-01-01 00:00:00).
      If this parameter is omitted, all usage records until now will be 
      returned.
      
    Return value:
      This method returns usage statistics for the given connection.
    """
    return _getConnection(id).usageStatistics.info(type, after, before)

from elements import _getElement
from connections import _getConnection
from .. import currentUser, elements, connections