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

from tomato.auth import User

def login(username, password): #@UnusedVariable, pylint: disable-msg=W0613
	"""
	Authenticates a user.
	
	@type username: string
	@param username: The users name  
	@type password: string
	@param password: The users password  
	@rtype: generic.User
	@raise fault.Error: when the user does not exist or the password is wrong 
	"""
	if username=="guest":
		return User(username, False, False)
	elif username=="admin":
		return User(username, True, True)
	else:
		return User(username, True, False)
