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

from ..lib.service import get_tomato_inner_proxy as _get_tomato_inner_proxy
from ..lib.settings import Config as _Config
from ..authorization import get_user_info as _get_user_info
from api_helpers import _getCurrentUserInfo

#fixme: should be obsolete after migration of user stuff to backend_users
def _getAccount(name):
	acc = _currentUser()
	if name and (not acc or name != acc.name):
		acc = getUser(name)
	_UserError.check(acc, code=_UserError.DENIED, message="No such user")
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
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthenticated")
	if name is None:
		name = _currentUserName()
	keys_to_show = _getCurrentUserInfo().info_visible_keys(_get_user_info(name))
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	info = api.user_info(name)
	for k in info:
		if k not in keys_to_show:
			del info[k]
	return info

def account_notifications(include_read=False):
	"""
	List notifications for the currently logged in user.

	:param bool include_read: include read notifications. if False, only return unread ones.
	:return: list of Notification
	"""
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthenticated")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	api.notification_list(_currentUserName(), include_read)

def account_notification_set_read(notification_id, read):
	"""
	Modify the read status of a notification

	:param str notification_id: ID of the notification to modify
	:param bool read: new read status of the notification
	:return: None
	"""
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthenticated")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	api.notification_set_read(_currentUserName(), read)

def account_list(organization=None, with_flag=None):
	"""
	Retrieves information about all accounts. 
	 
	Return value:
	  A list with information entries of all accounts. Each list entry contains
	  exactly the same information as returned by :py:func:`account_info`.
	"""
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthenticated")
	if organization is None:
		_UserError.check(_getCurrentUserInfo().may_list_all_users(), code=_UserError.DENIED, message="Unauthorized")
	else:
		_UserError.check(_getCurrentUserInfo().may_list_organization_users(organization), code=_UserError.DENIED, message="Unauthorized")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	return api.user_list(organization, with_flag, asUser=_currentUserName())

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
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthenticated")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	if name is None:
		name = _currentUserName()
	modify_allowed_list = _getCurrentUserInfo().modify_allowed_keys(_get_user_info(name))

	# check authorization for keys
	for k in attrs.iterkeys():
		if k not in modify_allowed_list:
			if ignore_key_on_unauthorized:
				del attrs[k]
			else:
				_UserError.check(False, code=_UserError.DENIED, message="trying to modify a key that is not allowed", data={"allowed_keys": modify_allowed_list, "attrs.keys()": attrs.keys()})

	# check authorization for flags
	if 'flags' in attrs:
		flags = attrs['flags']
		allowed_flags = _getCurrentUserInfo().modify_allowed_flags(_get_user_info(name))
		for k in flags.iterkeys():
			if k not in allowed_flags:
				if ignore_key_on_unauthorized:
					del flags[k]
				else:
					_UserError.check(False, code=_UserError.DENIED, message="trying to modify a flag that is not allowed", data={"allowed_flags": allowed_flags, "flags.keys()": flags.keys()})

	_get_user_info(name).invalidate_info()
	return api.user_modify(name, attrs)
		
def account_create(username, password, organization, attrs=None, provider=""):
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
	# fixme: use backend_users
	if not attrs: attrs = {}
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
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthenticated")
	if name is None:
		name = _currentUserName()
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	_UserError.check(_getCurrentUserInfo().may_delete(_get_user_info(name)), code=_UserError.DENIED, message="Unauthorized")
	api.user_remove(name)


def account_send_notification(name, subject, message, ref=None, from_support=False, subject_group=None):
	"""
	Sends an email to the account
	"""
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthorized")
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	if from_support:
		fromUser = None
	else:
		fromUser = _currentUserName()
	_UserError.check(_getCurrentUserInfo().may_send_message(_get_user_info(name)), code=_UserError.DENIED, message="not permission to send the message")
	api.send_message(name, subject, message, fromUser=fromUser, ref=ref, subject_group=subject_group)

def broadcast_announcement(title, message, ref=None, show_sender=True, subject_group=None, organization_filter=None):
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthorized")
	_UserError.check(_getCurrentUserInfo().may_broadcast_messages(organization_filter), code=_UserError.DENIED,
									message="No permission to broadcast to %s" % ("all users" if organization_filter is None else "this organization"))
	api = _get_tomato_inner_proxy(_Config.TOMATO_MODULE_BACKEND_USERS)
	api.broadcast_message(title, message, fromUser=(_currentUserName() if show_sender else None), ref=ref,
												subject_group=subject_group, organization_filter=organization_filter)

def account_usage(name): #@ReservedAssignment
	#fixme: backend_users and stuff
	_UserError.check(_currentUser(), code=_UserError.NOT_LOGGED_IN, message="Unauthorized")
	acc = _getAccount(name)
	return acc.totalUsage.info()


# the following functions should be removed, and clients should use the respective library in shared
		
def account_flags():
	"""
	Returns the dict of all account flags and their short descriptions.
	
	Return value:
	  A list of all available account flags.
	"""
	return flags

#deprecated
def account_flag_categories():
	"""
	Returns a dict which puts flags into different categories
	"""
	res = {}
	for cat in categories:
		res[cat['title']] = cat['flags']
	return res

def account_flag_configuration():
	return {
		'flags': flags,
		'categories': categories
		}





	
from host import _getOrganization
from .. import currentUser as _currentUser, currentUserName as _currentUserName
from ..lib.error import UserError as _UserError
from ..auth import getUser, flags, categories, register
