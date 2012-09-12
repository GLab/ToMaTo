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
import crypt, base64, hashlib
import subprocess

class Provider:
	"""
	.htpasswd auth provider
	
	This auth provider uses a .htpasswd file as an authentication backend.
	It reads the user credentials from the given file and compares the them to
	the given login credentials. If the credentials match to a user in the
	file, the username is compared to the given admin username (if that is not
	None or False). If the username is the same as the admin username the login
	is granted admin status.
	
	Note: .htpasswd files can be created and manipulated using the htpasswd command
	
	The auth provider takes the following options:
		file: The path of the .htpasswd file
		admin_user: The username of the admin user, defaults to None
	"""
	def __init__(self, file, admin_user=None):
		self.file = file
		self.admin_user = admin_user
	
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		lines = [l.rstrip().split(':', 1) for l in file(self.file).readlines()]
		lines = [l for l in lines if l[0] == username]
		if not lines:
			return None
		hashedPassword = lines[0][1]

		result = False
		if hashedPassword[:6] == '$apr1$':
			result = self.md5Validation(username, password, hashedPassword)
		elif hashedPassword[:5] == '{SHA}':
			result = self.sha1Validation(username, password, hashedPassword)
		elif len(hashedPassword) == 13:
			result = self.cryptValidation(username, password, hashedPassword)

		if result:
			return User(name = username, 
					is_admin = (self.admin_user != None and 
								username == self.admin_user))
		else:
			return None

	def cryptValidation(self, username, password, hashedPassword):
		if hashedPassword == crypt.crypt(password, hashedPassword[:2]):
			return True
		else:
			return False

	def md5Validation(self, username, password, hashedPassword):
		salt = hashedPassword.split('$')[2]
		command = ['openssl', 'passwd', '-apr1', '-salt', salt, password]
		generated = subprocess.check_output(command).rstrip()

		if hashedPassword == generated:
			return True
		else:
			return False

	def sha1Validation(self, username, password, hashedPassword):
		generated = base64.encodestring( 
							hashlib.sha1(password).digest() ).rstrip()
		if hashedPassword[5:] == generated:
			return True
		else:
			return False

	
def init(**kwargs):
	return Provider(**kwargs)
