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

from ..dumpmanager import api_errordump_info, api_errordump_list, api_errorgroup_info, api_errorgroup_list, api_errorgroup_modify

def errordump_info(source, dump_id, include_data=False):
    return api_errordump_info(source, dump_id, include_data)

def errordump_list(group_id=None, source=None, data_available=None):
    return api_errordump_list(group_id, source, data_available)

def errorgroup_info(group_id, include_dumps=False):
    return api_errorgroup_info(group_id, include_dumps)

def errorgroup_list():
    return api_errorgroup_list()

def errorgroup_modify(group_id, attrs):
    return api_errorgroup_modify(group_id, attrs)