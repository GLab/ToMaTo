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

from .. import elements
import generic

class Repy(generic.VMElement):
	TYPE = "repy"
	DIRECT_ATTRS_EXCLUDE = ["ram", "diskspace", "cpus", "bandwidth"]
	CAP_CHILDREN = {
		"repy_interface": [generic.ST_CREATED, generic.ST_PREPARED],
	}
	PROFILE_ATTRS = ["ram", "diskspace", "cpus", "bandwidth"]
	
	class Meta:
		db_table = "tomato_repy"
		app_label = 'tomato'
	
class Repy_Interface(generic.VMInterface):
	TYPE = "repy_interface"
	CAP_PARENT = [Repy.TYPE]
	
	class Meta:
		db_table = "tomato_repy_interface"
		app_label = 'tomato'
	
elements.TYPES[Repy.TYPE] = Repy
elements.TYPES[Repy_Interface.TYPE] = Repy_Interface