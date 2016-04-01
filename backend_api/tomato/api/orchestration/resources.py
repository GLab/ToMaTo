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

from backend_api.tomato.api.templates import template_list
from backend_api.tomato.api.profile import profile_list
from backend_api.tomato.api.network import network_list
from backend_api.tomato.api.network_instance import network_instance_list

def resources_map():
	return {
		'templates': template_list(),
		'profiles': profile_list(),
		'networks': network_list(),
		'network_instances': network_instance_list()
	}









