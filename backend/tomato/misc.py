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

from . import config, currentUser
from auth import Flags, mailFlaggedUsers, getUser

def getPublicKey():
	lines = []
	ignore = False
	with open(config.CERTIFICATE) as key:
		for line in key:
			if "PRIVATE" in line:
				ignore = not ignore
			elif not ignore:
				lines.append(line)
	return "".join(lines)

def getExternalURLs():
	return config.EXTERNAL_URLS

def mailAdmins(subject, text, global_contact = True, issue="admin"):
	user = currentUser()
	flag = None
	
	if global_contact:
		if issue=="admin":
			flag = Flags.GlobalAdminContact
		if issue=="host":
			flag = Flags.GlobalHostContact
	else:
		if issue=="admin":
			flag = Flags.OrgaAdminContact
		if issue=="host":
			flag = Flags.OrgaHostContact
	
	if flag is None:
		fault.raise_("issue '%s' does not exist" % issue)
	
	mailFlaggedUsers(flag, "Message from %s: %s" % (user.name, subject), "The user %s <%s> has sent a message to all administrators.\n\nSubject:%s\n%s" % (user.name, user.email, subject, text), organization=user.organization)
	
def mailUser(user, subject, text):
	from_ = currentUser()
	to = getUser(user)
	fault.check(to, "User not found")
	to.sendMail("Message from %s: %s" % (from_.name, subject), "The user %s has sent a message to you.\n\nSubject:%s\n%s" % (from_.name, subject, text))
	
from . import fault