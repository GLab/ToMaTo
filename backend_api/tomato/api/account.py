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

from ..authorization import PermissionChecker, get_pseudo_user_info
from api_helpers import getCurrentUserInfo, getCurrentUserName
from ..lib.remote_info import get_user_info, get_user_list, UserInfo

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
	if name is None:
		name = getCurrentUserName()
	target_account = get_user_info(name)
	keys_to_show = getCurrentUserInfo().account_info_visible_keys(target_account)
	info = target_account.info(update=True)
	for k in info.keys():
		if k not in keys_to_show:
			del info[k]
	return info

def account_list(organization=None, with_flag=None):
	"""
	Retrieves information about all accounts. 
	 
	Return value:
	  A list with information entries of all accounts. Each list entry contains
	  exactly the same information as returned by :py:func:`account_info`.
	"""
	if organization is None:
		getCurrentUserInfo().check_may_list_all_users()
	else:
		getCurrentUserInfo().check_may_list_organization_users(organization)
	return get_user_list(organization, with_flag)

def account_modify(name=None, attrs=None, ignore_key_on_unauthorized=False, ignore_flag_on_unauthorized=False):
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

	  ``flags`` must be a dictionary of the form {flag_name: is_set}.
	  if is_set is true, the respective flag will be set. if is_set is false, it will be unset.
	  if a flag is not mentioned in the dict, it is left as it is.

	Parameter *ignore_key_on_unauthorized*:
	  Defines the behavior when ``attrs`` contains a key that the current user
	  is not allowed to modify:
	  If True, the key is simply skipped, and the other keys are still modified.
	  If False, the whole operation will be cancelled.

	Parameter *ignore_flag_on_unauthorized*:
	  Similar to ``ingnore_key_on_unauthorized``, but with the ``flags`` attribute
	  
	Return value:
	  This method returns the info dict of the account. All changes will be 
	  reflected in this dict.
	"""
	if not attrs: attrs = {}
	if name is None:
		name = getCurrentUserName()
	target_account = get_user_info(name)
	modify_keys_allowed_list = getCurrentUserInfo().modify_user_allowed_keys(target_account)
	modify_flags_allowed = getCurrentUserInfo().modify_user_allowed_flags(target_account)

	attrs = PermissionChecker.reduce_keys_to_allowed(attrs, modify_keys_allowed_list, modify_flags_allowed,
																									 ignore_key_on_unauthorized, ignore_flag_on_unauthorized)

	return target_account.modify(attrs)
		
def account_create(username, password, organization, attrs=None):
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
	if getCurrentUserName() is None:
		attrs = PermissionChecker.reduce_keys_to_allowed(attrs,
																												PermissionChecker.account_register_self_allowed_keys(),
																												[])
	else:
		target_user = get_pseudo_user_info(username, organization)
		getCurrentUserInfo().check_may_create_user(target_user)
		attrs = PermissionChecker.reduce_keys_to_allowed(attrs,
																										 getCurrentUserInfo().modify_user_allowed_keys(target_user),
																										 getCurrentUserInfo().modify_user_allowed_flags(target_user))
	email = attrs.get('email', None)
	del attrs['email']  # fixme: email should be an api parameter here
	return UserInfo.create(username, organization, email, password, attrs)

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
	if name is None:
		name = getCurrentUserName()
	target_account = get_user_info(name)
	getCurrentUserInfo().check_may_delete_user(target_account)
	target_account.remove()


def account_usage(name): #@ReservedAssignment
	target_user = get_user_info(name)
	getCurrentUserInfo().check_may_view_user_usage(target_user)
	return target_user.get_usage()
