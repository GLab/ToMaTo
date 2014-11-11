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
import hashlib

class Provider(AuthProvider):
	"""
	dict auth provider
	
	This auth provider uses given user dicts as authentication data.
	Before checking the credentials the password is first converted using a 
	given hash function. If the hash option is set to None or False, the raw
	password will be checked against the database.
	
	Note: The dicts should contain username: password entries.
	
	The auth provider takes the following options:
		users: The dict containing username: passsword pairs for normal users,
		       defaults to {}
		organization: The organization that the users belong to
		flags: A list of flags to assign to all users
	    hash: The hash method use for passwords, defaults to "sha1"
	"""
	def parseOptions(self, users=None, organization=None, flags=None, hash="sha1", **kwargs): #@ReservedAssignment
		if not users: users = {}
		if not flags: flags = []
		self.users = users
		self.flags = flags
		self.hash = hash
		self.organization = getOrganization(organization)
	
	def _hash(self, hash, data): #@ReservedAssignment
		h = hashlib.new(hash)
		h.update(data)
		return h.hexdigest()
	
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		if self.hash:
			password = self._hash(self.hash, password)
		if username in self.users and self.users[username] == password:
			return User.create(name=username, flags=self.flags, organization=self.organization)
		return False

def init(**kwargs):
	return Provider(**kwargs)

from ..host import getOrganization