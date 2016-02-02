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

from ..auth import User, Provider as AuthProvider
import crypt

class Provider(AuthProvider):
	"""
	.htpasswd auth provider
	
	This auth provider uses a .htpasswd file as an authentication backend.
	It reads the user credentials from the given file and compares the them to
	the given login credentials.
	
	Note: .htpasswd files can be created and manipulated using the htpasswd command
	
	The auth provider takes the following options:
		file: The path of the .htpasswd file
		organization: The organization that the users belong to
		flags: The flags to assign to all users
	"""
	def parseOptions(self, file, organization=None, flags=None, **kwargs): #@ReservedAssignment
		if not flags: flags = []
		self.file = file
		self.flags = flags
		self.organization = getOrganization(organization)
	
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		lines = [l.rstrip().split(':', 1) for l in file(self.file).readlines()]
		lines = [l for l in lines if l[0] == username]
		if not lines:
			return None
		hashedPassword = lines[0][1]
		if not hashedPassword == crypt.crypt(password, hashedPassword[:2]):
			return None
		return User.create(name=username, flags=self.flags, organization=self.organization)
	
def init(**kwargs):
	return Provider(**kwargs)

from ..host import getOrganization