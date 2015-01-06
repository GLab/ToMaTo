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

from django.shortcuts import render

import json

from lib import wrap_rpc

@wrap_rpc
def console(api, request, id): #@ReservedAssignment
	info=api.element_info(id)
	top=api.topology_info(info["topology"])
	return render(request, "element/console.html", {'info': info, 'top': top})

@wrap_rpc
def console_novnc(api, request, id): #@ReservedAssignment
	info=api.element_info(id)
	top=api.topology_info(info["topology"])
	return render(request, "element/console_novnc.html", {'info': info, 'top': top})
		
@wrap_rpc
def rextfv_status(api, request, id): #@ReservedAssignment
	return render(request, "element/rextfv_status.html", {'id': id})
