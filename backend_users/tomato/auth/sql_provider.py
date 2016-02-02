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
from django.db import connections

class Provider(AuthProvider):
	"""
	SQL auth provider
	
	This auth provider uses SQL as an authentication backend. It executes an
	SQL query to check the user credentials and accepts the login if the query
	result contains at least one row. 
	In the queries, the keywords :username and :password will be substituted by
	the login credentials.
	Before checking the credentials the password is first converted using a 
	given hash function. If the hash option is set to None or False, the raw
	password will be checked against the database.
	
	Note: To use an additional database for this provider the database can be
	      configured via DATABASES. Only the entry named default will be used
	      by ToMaTo itself, the other databases can be used for authentication
	      or other modules.
	
	The auth provider takes the following options:
		query: An SQL query to use to check for a user in the database.
		flags: A list of flags to assign
		database: The database backend to use, as configured in the config
		          in DATABASES, defaults to "default"
		organization: The organization that the users belong to
	    hash: The hash method use for passwords, defaults to "sha1"
	"""
	def parseOptions(self, query, organization=None, database="default", flags=None, hash="sha1", **kwargs): #@ReservedAssignment
		if not flags: flags = []
		self.hash = hash
		self.database = database
		self.query = query
		self.flags = flags
		self.organization = getOrganization(organization)
	
	def _hash(self, hash, data): #@ReservedAssignment
		h = hashlib.new(hash)
		h.update(data)
		return h.hexdigest()
	
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		if self.hash:
			password = self._hash(self.hash, password)
		cursor = connections[self.database].cursor()
		cursor.execute(self.query, {"username":username, "password":password})
		if cursor.fetchone():
			return User.create(name=username, flags=self.flags, organization=self.organization)
		return False

def init(**kwargs):
	return Provider(**kwargs)

from ..host import getOrganization