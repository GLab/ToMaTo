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

from ..db import *

from ..lib.error import UserError

# noinspection PyClassHasNoInit
class Role:
	owner = "owner" # full topology control, permission changes, topology removal 
	manager = "manager" # full topology control, no topology delete, no permission changes
	user = "user" # no destroy/prepare, no topology changes, no permission changes
	null = "null" # no access at all
	
	RANKING=[null, user, manager, owner]
	
def role_descriptions():
	return {
		Role.owner:	{	'title': "Owner",
						'description':"full topology control, permission changes, topology removal"},
					
		Role.manager:{	'title': "Manager",
						'description':"full topology control, no topology delete, no permission changes"},
					
		Role.user:	{	'title': "User",
						'description':"no destroy/prepare, no topology changes, no permission changes"},
					
		Role.null:	{	'title': "[no permission]",
						'description':"no access at all"}
	}
	

class Permission(ExtDocument, EmbeddedDocument):
	"""
	:type user: auth.User
	:type role: str
	"""
	from . import User
	user = ReferenceField(User, required=True)
	role = StringField(choices=['owner', 'manager', 'user'], required=True)


# noinspection PyClassHasNoInit
class PermissionMixin(object):
	"""
	:type permissions: list of Permission
	"""
	permissions = []
	del permissions

	def getRole(self, user=None):
		"""
		:type user: auth.User or None
		"""
		if not user:
			user = currentUser()
		if user is True:
			return Role.owner
		role = Role.null
		# Global permissions, that's easy
		if user.hasFlag(Flags.GlobalToplUser):
			role = Role.user
		if user.hasFlag(Flags.GlobalToplManager):
			role = Role.manager
		if user.hasFlag(Flags.GlobalToplOwner):
			role = Role.owner

		# User specific role
		for perm in self.permissions:
			if perm.user != user:
				continue
			if Role.RANKING.index(perm.role) > Role.RANKING.index(role):
				role = perm.role

		# Organization role
		orgaRole = Role.null
		if user.hasFlag(Flags.OrgaToplUser):
			orgaRole = Role.user
		if user.hasFlag(Flags.OrgaToplManager):
			orgaRole = Role.manager
		if user.hasFlag(Flags.OrgaToplOwner):
			orgaRole = Role.owner
		if Role.RANKING.index(orgaRole) > Role.RANKING.index(role):
			for perm in self.permissions:
				if perm.role == Role.owner and perm.user.organization == user.organization:
					role = orgaRole
					break

		return role
	
	def hasRole(self, role=Role.user, user=None):
		r = self.getRole(user)
		return Role.RANKING.index(r) >= Role.RANKING.index(role)		
	
	def checkRole(self, user=None):
		UserError.check(self.hasRole(user), code=UserError.DENIED, message="Not enough permissions")

	def setRole(self, user=None, role=Role.user):
		if not user:
			user = currentUser()
		self.permissions = 	filter(lambda perm: perm.user != user, self.permissions)
		self.permissions.append(Permission(user=user, role=role))

from . import Flags
