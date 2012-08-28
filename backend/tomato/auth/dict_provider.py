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
	dict auth provider
	
	This auth provider uses given user dicts as authentication data.
	Two seperate dicts called users and admins are used for respective
	logins. If the given login ceredntials are found in the admin dict, the 
	user dict is not checked and the login is grated with admin rights.
	Before checking the credentials the password is first converted using a 
	given hash function. If the hash option is set to None or False, the raw
	password will be checked against the database.
	
	Note: The dicts should contain username: password entries.
	
	The auth provider takes the following options:
		users: The dict containing username: passsword pairs for normal users,
		       defaults to {}
		admins: The dict containing username: passsword pairs for admin users
		       defaults to {}
	    hash: The hash method use for passwords, defaults to "sha1"
	"""
	def __init__(self, users={}, admins={}, hash=None): #@ReservedAssignment
		self.users = users
		self.admins = admins
		self.hash = hash
	
	def _hash(self, hash, data): #@ReservedAssignment
		h = hashlib.new(hash)
		h.update(data)
		return h.hexdigest()
	
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		if self.hash:
			password = self._hash(self.hash, password)
		if username in self.users and self.users[username] == password:
			return User(name=username, is_admin=True)
		if username in self.admins and self.admins[username] == password:
			return User(name=username)
		return False

def init(**kwargs):
	return Provider(**kwargs)