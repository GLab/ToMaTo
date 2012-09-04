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

from django.db import models

from tomato.auth import User, Flags
from tomato import currentUser, fault

class Role:
    owner = "owner" # full topology control, permission changes, topology removal 
    manager = "manager" # full topology control, no topology delete, no permission changes
    user = "user" # no destroy/prepare, no topology changes, no permission changes
    external = "external" # no access at all
    
    RANKING=[owner, manager, user, external]
    

class Permissions(models.Model):

    class Meta:
        db_table = "tomato_permissions"
        app_label = 'tomato'

    def set(self, user, role): #@ReservedAssignment
        try:
            entry = self.entries.get(user=user)
            entry.role = role
            entry.save()
        except PermissionEntry.DoesNotExist:
            entry = PermissionEntry(set=self, user=user, role=role)
            entry.save()
            


class PermissionEntry(models.Model):
    set = models.ForeignKey(Permissions, null=False, related_name="entries") #@ReservedAssignment
    user = models.ForeignKey(User, null=False)
    role = models.CharField(max_length=20)

    class Meta:
        db_table = "tomato_permissionentry"
        app_label = 'tomato'
        unique_together = (("user", "set"),)
    
    
    
def _globalRole(user):
    if user.hasFlag(Flags.GlobalOwner):
        return Role.owner
    if user.hasFlag(Flags.GlobalManager):
        return Role.manager
    if user.hasFlag(Flags.GlobalUser):
        return Role.user
    return Role.external
    
    

class PermissionMixin:
    #permissions: Permissions
    
    def getRole(self, user=None):
        if not user:
            user = currentUser()
        globalRole = _globalRole(user)
        try:
            role = self.permissions.entries.get(user=user).role
            return role if Role.RANKING.index(globalRole) >= Role.RANKING.index(role) else globalRole
        except PermissionEntry.DoesNotExist:
            return globalRole
    
    def hasRole(self, role=Role.user, *args, **kwargs):
        r = self.getRole(*args, **kwargs)
        return Role.RANKING.index(r) <= Role.RANKING.index(role)        
    
    def checkRole(self, *args, **kwargs):
        fault.check(self.hasRole(*args, **kwargs), "Not enough permissions")