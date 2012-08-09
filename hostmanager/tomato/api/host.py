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

def host_info():
    return {
        "hostmanager": {
            "version": 0.1,
        },
        "site": "ukl",
        "coordinates": [0, 0],
    }

def host_capabilities():
    return {
        "element_types": dict([(type_, {}) for type_ in tomato.elements.TYPES]),
        "resource_types": dict([(type_, {}) for type_ in tomato.resources.TYPES]),
    }

import tomato.elements
import tomato.resources