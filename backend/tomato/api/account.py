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
	if name and (not acc or name != acc.name):
		acc = getUser(name)
	fault.check(acc, "No such user")
	return acc

def account_info(name=None):
	"""
	Retrieves information about an account.
	
	Parameter *name*:
	  If this parameter is given, information about the given account will
	  be returned. Otherwise information about the current user will be 
	  returned.
	  
	Return value:
	  The return value of this method is a dict containing the following 
	  information about the account:
	  
	  ``name``
		The name of the account.
		
	  ``origin``
		The origin of the account.
	  
	  ``id``
		The unique id of the account in the format ``Name@Origin``.
		
	  ``flags``
		The flags of the account.
	  
	  ``realname``
		The real name of the account holder.
		
	  ``affiliation``
		The affiliation of the account holder, e.g. university, company, etc.
	  
	  ``email``
		The email address of the account holder. This address wil be used to 
		send important notifications.
		
	Exceptions:
	  If the given account does not exist an exception is raised.
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	acc = _getAccount(name)
	return acc.info(currentUser() == acc or currentUser().isAdminOf(acc))

def account_list(organization=None):
	"""
	Retrieves information about all accounts. 
	 
	Return value:
	  A list with information entries of all accounts. Each list entry contains
	  exactly the same information as returned by :py:func:`account_info`.
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	if organization:
		organization = _getOrganization(organization)
	if currentUser().hasFlag(Flags.GlobalAdmin):
		accounts = getAllUsers(organization=organization) if organization else getAllUsers()
		return [acc.info(True) for acc in accounts]
	elif currentUser().hasFlag(Flags.OrgaAdmin):
		if organization != currentUser().organization:
			fault.raise_("Not enough permissions")
		return [acc.info(True) for acc in getAllUsers(organization=currentUser().organization)]
	else:
		fault.raise_("Not enough permissions")

def account_modify(name=None, attrs={}):
	"""
	Modifies the given account, configuring it with the given attributes.
	
	Parameter *name*:
	  If this parameter is given, the given user will be modified. Otherwise
	  the currently logged in user will be modified. Note that only users with
	  the flag ``admin`` are permitted to modify other accounts.
	
	Parameter *attrs*:
	  This field contains a dict of attributes to set/overwrite on the account.
	  Users can change the following fields of their own accounts:
	  ``realname``, ``affiliation``, ``password`` and ``email``.
	  Administrators (i.e. users with flag ``admin``) can additionally change
	  these fields on all accounts: ``name``, ``origin`` and ``flags``.
	  
	Return value:
	  This method returns the info dict of the account. All changes will be 
	  reflected in this dict.
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	acc = _getAccount(name)
	if acc != currentUser():
		fault.check(currentUser().isAdminOf(acc), "No permissions")
	acc.modify(attrs)
	return acc.info(True)
		
def account_create(username, password, organization, attrs={}, provider=""):
	"""
	This method will create a new account in a provider that supports this.
	
	Note that this method like all others is only available for registered 
	users. Backend configurations should include a guest account to enable
	user registration.  
	 
	Parameter *username*:
	  This field must contain the requested user name of the new user.
	
	Parameter *password*:
	  This field must contain the password for the new user.
	
	Parameter *attrs*:
	  This field can contain additional attributes for the account like the 
	  ones accepted in :py:func:`account_modify`.
	
	Parameter *provider*:
	  If multiple providers support account registration, this field can be 
	  used to create the account in one specific provider. If this field is
	  not given, all providers will be queried in turn. 
	
	Return value:
	  This method returns the info dict of the new account.
	"""
	user = register(username, password, organization, attrs, provider)
	return user.info(True)
		
def account_remove(name=None):
	"""
	Deletes the given account from the database. Note that this does not remove
	the entry in any external user database. Thus the user can still login 
	which will create a new account.
	
	Parameter *name*:
	  This field must contain the user name of the account to be removed.
	
	Return value:
	  This method returns nothing if the account has been deleted.
	"""
	if not currentUser():
		raise ErrorUnauthorized()
	acc = _getAccount(name)
	fault.check(currentUser().isAdminOf(acc), "No permissions")
	if acc == currentUser() and acc.hasFlag(Flags.GlobalAdmin):
		fault.raise_("Admins must not delete themselves", fault.USER_ERROR)	
	remove(acc)
		
def account_flags():
	"""
	Returns the dict of all account flags and their short descriptions.
	
	Return value:
	  A list of all available account flags.
	"""
	return flags

def account_flag_categories():
	"""
	Returns a dict which puts flags into different categories
	"""
	return categories
		
from host import _getOrganization
from .. import fault, currentUser
from ..auth import getUser, getAllUsers, flags, categories, register, remove, Flags
from ..lib.rpc import ErrorUnauthorized  #@UnresolvedImport