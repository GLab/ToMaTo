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


def _getAccount(name):
    acc = currentUser()
    if name and name != acc.name:
        acc = getUser(name)
    fault.check(acc, "No such user")
    return acc

def account_info(name=None):
    """
    undocumented
    """
    acc = _getAccount(name)
    return acc.info()

def account_list():
    """
    undocumented
    """
    return [acc.info() for acc in getAllUsers()]

def account_modify(name=None, attrs={}):
    """
    undocumented
    """
    acc = _getAccount(name)
    if name and name != currentUser().name:
        fault.check(currentUser().hasFlag(Flags.Admin), "No permissions")
    acc.modify(attrs)
        
def account_create(username, password, attrs={}, provider=""):
    """
    undocumented
    """
    user = register(username, password, attrs, provider)
    return user.info()
        
def account_change_password(password):
    """
    undocumented
    """
    changePassword(password)
        
def flags():
    """
    undocumented
    """
    return [getattr(Flags, flag) for flag in dir(Flags) if not flag.startswith("__")]
        
from .. import fault, currentUser
from ..auth import getUser, getAllUsers, Flags, register, changePassword