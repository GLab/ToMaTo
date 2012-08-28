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
    el = elements.get(id_)
    fault.check(el, "Element with id #%d does not exist", id_)
    return el

def element_create(top, type, parent=None, attrs={}): #@ReservedAssignment
    top = _getTopology(top)
    if parent:
        parent = _getElement(parent)
    el = elements.create(top, type, parent, attrs)
    return el.info()

def element_modify(id, attrs): #@ReservedAssignment
    el = _getElement(id)
    el.modify(attrs)
    return el.info()

def element_action(id, action, params={}): #@ReservedAssignment
    el = _getElement(id)
    return el.action(action, params)

def element_remove(id): #@ReservedAssignment
    el = _getElement(id)
    el.remove()
    return {}

def element_info(id): #@ReservedAssignment
    el = _getElement(id)
    return el.info()
    

from tomato import fault, elements
from topology import _getTopology