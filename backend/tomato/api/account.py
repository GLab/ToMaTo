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
    if name:
        fault.check(acc.hasFlag(Flags.Admin), "No permissions")
        acc = getUser(name)
    fault.check(acc, "No such user")
    return acc

def account_info(name=None):
    acc = _getAccount(name)
    return acc.info()

def account_list():
    return [acc.info() for acc in getAllUsers()]

def account_modify(name=None, attrs={}):
    acc = _getAccount(name)
    acc.modify(attrs)
        
def account_create(username, password, attrs={}, provider=""):
    user = register(username, password, attrs, provider)
    return user.info()
        
def account_change_password(password):
    changePassword(password)
        
from .. import fault, currentUser
from ..auth import getUser, getAllUsers, Flags, register, changePassword