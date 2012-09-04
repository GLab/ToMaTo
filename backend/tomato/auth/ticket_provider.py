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
import hashlib

class Provider:
	"""
	Ticket auth provider
	
	This auth provider uses a ticket mechanism for authentication.
	With this auth provider arbitrary users will be accepted as long as their
	password consists of a valid user ticket or admin ticket.
	Tickets are calculated as a hash value of the username together with a 
	secret key.		TICKET = hash(USERNAME + SECRET)
	Two seperate secret keys exist for admin login and user login. If either
	of these keys is None or False the respective login is disabled.
	Note: If both keys are the same all valid logins will get admin status.
	The hash algorithm that should be used can be configured.
	
	Security note: Anyone that has access to either secret key can create
	               valid login tickets arbitrarily.
	
	The auth provider takes the following options:
		admin_secret: The secret key to use for admin login, defaults to None
		user_secret: The secret key to use for user login, default to None
	    hash: The hash method use for passwords, defaults to "sha1"
	"""
	def __init__(self, user_secret=None, admin_secret=None, hash="sha1"): #@ReservedAssignment
		self.hash = hash
		self.user_secret = user_secret
		self.admin_secret = admin_secret
	
	def _hash(self, hash, data): #@ReservedAssignment
		h = hashlib.new(hash)
		h.update(data)
		return h.hexdigest()
	
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		if self.admin_secret and self._hash(self.hash, username + self.admin_secret) == password:
			return User.create(name=username, admin=True)
		if self.user_secret and self._hash(self.hash, username + self.user_secret) == password:
			return User.create(name=username)
		return False

def init(**kwargs):
	return Provider(**kwargs)