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
	Ticket auth provider
	
	This auth provider uses a ticket mechanism for authentication.
	With this auth provider arbitrary users will be accepted as long as their
	password consists of a valid user ticket.
	Tickets are calculated as a hash value of the username together with a 
	secret key.		TICKET = hash(USERNAME + SECRET)
	The hash algorithm that should be used can be configured.
	
	Security note: Anyone that has access to either secret key can create
	               valid login tickets arbitrarily.
	
	The auth provider takes the following options:
		secret: The secret key to use for user login, defaults to None
		flags: The list of flags that users get.
	    hash: The hash method use for passwords, defaults to "sha1"
		organization: The organization that the users belong to
	"""
	def parseOptions(self, secret, organization=None, flags=None, hash="sha1", **kwargs): #@ReservedAssignment
		if not flags: flags = []
		self.hash = hash
		self.secret = secret
		self.flags = flags
		self.organization = getOrganization(organization)
	
	def _hash(self, hash, data): #@ReservedAssignment
		h = hashlib.new(hash)
		h.update(data)
		return h.hexdigest()
	
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		if self._hash(self.hash, username + self.secret) == password:
			return User.create(name=username, flags=self.flags, organization=self.organization)
		return False

def init(**kwargs):
	return Provider(**kwargs)

from ..host import getOrganization