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
import tomato.config as config
import crypt

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
	lines = [l.rstrip().split(':', 1) for l in file(config.auth_htpasswd_file).readlines()]
	lines = [l for l in lines if l[0] == username]
	if not lines:
		return None
	hashedPassword = lines[0][1]
	if not hashedPassword == crypt.crypt(password, hashedPassword[:2]):
		return None
	return User(username, True, username == config.auth_htpasswd_admin_user)