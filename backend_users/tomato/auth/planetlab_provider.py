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
import xmlrpclib

class Provider(AuthProvider):
	"""
	Planetlab auth provider
	
	This auth provider uses a Planetlab server as an authentication backend.
	It uses the login credentials to login to the given server and to read the
	user data if he exists.
	If the site_filter is given only users of these sites will be allowed.
	If accept_admin is True planetlab users with the admin role will be granted
	admin privileges. 
	
	The auth provider takes the following options:
		api_uri: The PLCAPI URI, i.e.: https://host:port/PLCAPI/
		site_filter: A site abbreviation or list of site abbreviations to allow
		             access.
		organization: The organization that the users belong to
		roles: ...
	"""
	def parseOptions(self, api_uri, organization=None, site_filter=None, roles=None, **kwargs):
		if not roles: roles = {"user": []}
		self.api_uri = api_uri
		self.site_filter = site_filter
		if isinstance(self.site_filter, str):
			self.site_filter = [self.site_filter]
		self.roles = roles
		self.organization = getOrganization(organization)
		
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		try:
			api = xmlrpclib.ServerProxy(self.api_uri)
			try:
				auth = {"AuthMethod":"password", "Username":username, "AuthString": password}
				persons = api.GetPersons(auth, username)
				if len(persons) != 1:
					return False
				if self.site_filter:
					sites = [s["abbreviated_name"] for s in api.GetSites(auth, persons[0]["site_ids"])]
					if not (set(self.site_filter) & set(sites)):
						return False
				flags = []
				accept = False
				roles = persons[0]["roles"]
				for role in roles:
					if role in self.roles:
						flags.append(self.roles[role])
						accept = True
				if accept:
					return User.create(name=username, email=username, flags=flags, organization=self.organization)
				else:
					return False
			except Exception, errormessage:
				return False
		except Exception, errormessage:
			print "Failed to bind to server: %s" % errormessage
			return False
	
def init(**kwargs):
	return Provider(**kwargs)

from ..host import getOrganization