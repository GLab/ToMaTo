# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Andreas Teuchert, University of Kaiserslautern
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

import ldap

class Provider(AuthProvider):
	"""
	LDAP auth provider
	
	This auth provider uses LDAP as an authentication backend.
	The LDAP server can be configured with the server_uri option. If the server
	uses SSL, the server_cert option can be used to configure the public server
	certificate.
	In the first authentication step a connection is established to the server
	using bind_dn and bind_pw to check that the user exists below the given 
	identity_base path and read the user properties.
	If the user exists, a direct connection is established to the server using
	the determined user DN and the login password to check the password.
	If the password is correct, two more queries are made the server to get the
	members of the given admin and user groups and check if the user DN is
	if listed as a member of these groups.
	
	The auth provider takes the following options:
		server_uri: The URI of the server. This normally starts with ldap:// or
		            ldaps://, which determines the usage of SSL.
		server_cert: The location of the server certificate to use for SSL
		bind_dn: The DN of a bind user to check the username
		bind_pw: The password of the bind user
		identity_base: The base path for all identities
		groups: A dict of group/flags pairs where the user DN must be part of 
		  the group to match and get thne flags.
	"""
	def parseOptions(self, server_uri, server_cert, bind_dn, bind_pw, identity_base, groups, **kwargs):
		self.server_uri = server_uri
		self.server_cert = server_cert
		self.bind_dn = bind_dn
		self.bind_pw = bind_pw
		self.identity_base = identity_base
		self.groups = groups

	def _ldap_conn(self):
		ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
		ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
		ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.server_cert)
		try:
			conn = ldap.initialize(uri=self.server_uri)
			conn.simple_bind(who=self.bind_dn, cred=self.bind_pw)
		except ldap.LDAPError, error_message:
			raise Exception('Error binding to %s as %s: %s' % (self.server_uri, self.bind_dn, str(error_message)))
		return conn

	def login(self, username, password):
		data = self._get_user(username)
		if not data:
			return False
		userdn = data[0][0]
		email = data[0][1]['mail'][0]
		if not self._check_credentials(userdn, password):
			return False
		for group, flags in self.groups.iteritems():
			if self._is_in_group(userdn, group):
				return User.create(name=username, flags=flags, email=email)
		return False
		
	def _get_user(self, user):
		"""
		Verify if user exists. This method does NOT check a supplied password.
		"""
		conn = self._ldap_conn()
		try:
			user = conn.search_s(self.identity_base, ldap.SCOPE_SUBTREE, 'uid=%s' % user)
			if len(user) > 0:
				return user
			else:
				return None	
		except Exception, e: #pylint: disable-msg=W0703
			print 'LDAP search for user %s failed: %s' % (user, e)
			return None
		finally:
			conn.unbind_s()

	def _check_credentials(self, userdn, password):
		"""
		Check if a supplied password matches the user.
		"""
		conn = self._ldap_conn()
		try:
			conn = ldap.initialize(uri=self.server_uri)
			conn.simple_bind_s(who=userdn, cred=password)
			return True
		except ldap.LDAPError, error_message:
			print 'Authenticating user %s failed: %s' % (userdn, str(error_message))
			return False
		finally:
			conn.unbind_s()
		
	def _is_in_group(self, userdn, groupdn):
		conn = self._ldap_conn()
		try:
			members = conn.search_s(groupdn, ldap.SCOPE_SUBTREE, attrlist=['member'])
			if members[0][1].has_key('member'):
				return userdn in members[0][1]['member']
			else:
				print 'Group %s has no members.' % groupdn
				return False
		except ldap.LDAPError, error_message:
			print 'Authenticating user %s failed: %s' % (userdn, str(error_message))
			return False
		finally:
			conn.unbind_s()

def init(**kwargs):
	return Provider(**kwargs)