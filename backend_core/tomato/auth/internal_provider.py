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

from ..auth import User, Provider as AuthProvider, notifyFilteredUsers, Flags
from .. import setCurrentUser
from ..lib.error import UserError
from ..lib.settings import settings, Config

class Provider(AuthProvider):
	def parseOptions(self, allow_registration=True, default_flags=None, **kwargs):
		if not default_flags: default_flags = ["over_quota"]
		self.allow_registration = allow_registration
		self.default_flags = default_flags
	def login(self, username, password): #@UnusedVariable, pylint: disable-msg=W0613
		try:
			user = self.getUsers().get(name=username)
			if user.checkPassword(password):
				return user
			else:
				return False
		except User.DoesNotExist:
			return False
	def getPasswordTimeout(self):
		return None
	def canRegister(self):
		return self.allow_registration
	def canChangePassword(self):
		return True
	def changePassword(self, username, password):
		pass # password in user record will be changed by auth
	def register(self, username, password, organization, attrs):
		UserError.check(self.getUsers(name=username).count()==0, code=UserError.ALREADY_EXISTS, message="Username already exists")
		user = User.create(name=username, organization=organization, flags=self.default_flags, password=password, origin=self.name, **attrs)
		adminmsg = settings.get_email_settings(Config.EMAIL_NEW_USER_ADMIN)
		usermsg = settings.get_email_settings(Config.EMAIL_NEW_USER_WELCOME)
		notifyFilteredUsers(lambda u: u.hasFlag(Flags.GlobalAdminContact)
					or u.hasFlag(Flags.OrgaAdminContact) and user.organization == u.organization,
		            adminmsg['subject'], adminmsg['body'] % {'username': username}, ref=['account', username])
		user.sendNotification(usermsg['subject'], usermsg['body'] % {'username': username}, ref=['account', username])
		return user
		
def init(**kwargs):
	return Provider(**kwargs)