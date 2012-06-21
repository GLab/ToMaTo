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

def _top_access(top, role, user):
	"""
	NOT CALLABLE VIA XML-RPC
	Asserts the user has access to a topology.
	
	@type top: topology.Topology
	@param top: The topology
	@type role: string
	@param role: The minimal role the user must have, either "user" or "manager"
	@type user: generic.User
	@param user: The user object  
	@rtype: None
	@raise fault.Error: when the user does not have the required privileges 
	"""
	fault.check(top.checkAccess(role, user), "access to topology %s denied", top.id, code=fault.AUTHENTICATION_ERROR)

def _admin_access(user):
	"""
	NOT CALLABLE VIA XML-RPC
	Asserts the user has admin access.
	
	@type user: generic.User
	@param user: The user object  
	@rtype: None
	@raise fault.Error: when the user does not have the required privileges 
	"""
	fault.check(user.is_admin, "admin access denied", code=fault.AUTHENTICATION_ERROR)
	
from external_networks import *
from hosts import *
from misc import *
from templates import *
from topologies import *
from device_profiles import *