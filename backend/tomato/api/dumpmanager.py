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


def errordump_info(source, dump_id, include_data=False):
    """
    Returns details for the given dump.
    A dump is identified by its source, and the dump_id on this source.
    
    Parameter *source*:
      A string. This is the source (i.e., a certain host, or the backend) of the dump.
    
    Parameter *dump_id*: 
      The unique identifier of the dump to be queried. 
    
    Parameter *include_data*:
      A boolean.
      Every dump has environment data attatched to it. This data may be big (i.e., >1MB).
      By default, the data of a dump has most likely not been loaded from its source.
      If include_data is False, this data will not be returned by this call.
      If it is True, this data will first be fetched from the source, if needed, and included in this call's return.
    
    Return value:
      The return value of this method is the info dict of the dump.
      If include_data is True, it will contain a data field, otherwise a data_available indicator.
    """
    from ..dumpmanager import api_errordump_info
    return api_errordump_info(source, dump_id, include_data)

def errordump_list(group_id=None, source=None, data_available=None):
    """
    Returns a list of dumps.
    
    Parameter *group_id*: 
      A string. If this is not None, only dumps of this group will be included. 
    
    Parameter *source*:
      A string. If this is not None, only dumps from this source will be included.
    
    Parameter *data_available*:
      A boolean. If this is not None, only dumps which match this criterion will be included. 
      
    Return value:
      A list of dumps, filtered by the arguments.
    """
    from ..dumpmanager import api_errordump_list
    return api_errordump_list(group_id, source, data_available)

def errordump_remove(source, dump_id):
    """
    Remove a dump.
    
    Parameter *source*:
      A string. This is the source (i.e., a certain host, or the backend) of the dump.
    
    Parameter *dump_id*: 
      The unique identifier of the dump to be removed.
    """
    from ..dumpmanager import api_errordump_remove
    api_errordump_remove(source, dump_id)

def errorgroup_info(group_id, include_dumps=False):
    """
    Returns details for the given dump group.
    
    Parameter *group_id*:
      A string. The unique identifier of the group.
    
    Parameter *include_dumps*: 
      If true, a list of all dumps will be attached. 
    
    Return value:
      The return value of this method is the info dict of the group, maybe expanded by a list of dumps.
    """
    from ..dumpmanager import api_errorgroup_info
    return api_errorgroup_info(group_id, include_dumps)

def errorgroup_list(show_empty=False):
    """
    Returns a list of all error groups.
    """
    from ..dumpmanager import api_errorgroup_list
    return api_errorgroup_list(show_empty)

def errorgroup_modify(group_id, attrs):
    """
    Allows to modify the description of the error group.
    
    Parameter *group_id*:
      A string. The unique identifier of the group.
    
    Parameter *attrs*: 
      A dict with attributes to update. This matches the info dict.
      Only the description can be updated. 
    
    Return value:
      The return value of this method is the info dict of the group.
    """
    from ..dumpmanager import api_errorgroup_modify
    return api_errorgroup_modify(group_id, attrs)

def errorgroup_remove(group_id):
    """
    Remove a dump.
    
    Parameter *dump_id*: 
      The unique identifier of the group to be removed.
    """
    from ..dumpmanager import api_errorgroup_remove
    api_errorgroup_remove(group_id)
    
def errordumps_force_refresh():
    """
    Force a refresh of dumps.
    This is done automatically in a longer interval.
    To get instant access to all dumps, call this function.
    
    Return value:
      The time in seconds it takes until all dumps should be collected.
    """
    from ..dumpmanager import api_force_refresh
    return api_force_refresh()
