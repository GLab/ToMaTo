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

def _getTopology(id_):
    top = topology.get(id_)
    fault.check(top, "Topology with id #%d does not exist", id_)
    return top

def topology_create():
    return topology.create().info()

def topology_remove(id): #@ReservedAssignment
    top = _getTopology(id)
    top.remove()

def topology_modify(id, attrs): #@ReservedAssignment
    top = _getTopology(id)
    top.modify(attrs)
    return top.info()

def topology_action(id, action, params={}): #@ReservedAssignment
    top = _getTopology(id)
    return top.action(action, params)

def topology_info(id, full=False): #@ReservedAssignment
    top = _getTopology(id)
    return top.info(full)

def topology_list(full=False): #@ReservedAssignment
    tops = topology.getAll()
    return [top.info(full) for top in filter(lambda t:t.hasRole("user"), tops)]

def topology_permission(id, user, role): #@ReservedAssignment
    top = _getTopology(id)
    user = _getAccount(user)
    top.setRole(user, role)
    
from account import _getAccount
from tomato import fault, topology