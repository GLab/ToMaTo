from _shared import _getUser

def user_check_password(name, password):
	user = _getUser(name)
	return user.checkPassword(password)

def allowed_modify_keys(userA, userB):
	"""
	Return the list of attrs keys userA is allowed to modify when calling user_modify(userB)
	:param userA: username of user who is modifying
	:param userB: username of user who is modified
	:return: list of keys
	:rtype: list[str]
	"""
	#fixme: implement
	return []

def allowed_modify_flags(userA, userB):
	"""
	Return the list of permissions userA is allowed to modify for userB
	:param str userA: username of user who is modifying
	:param str userB:  username of user who is modified
	:return: list of permissions userA is allowed to modify
	:rtype: list(str)
	"""
	#fixme: implement
	return []

def allowed_view_details(userA, userB):
	"""
	check which details userA may see of userB (keys of the info() dict)
	when using user_info of user_list, you can use user_info(userB, userA) to
	automatically apply this.

	:param str userA: username of user who wants to see details
	:param str userB: username of user of which userA wants to see the details
	:return: keys userA may see about userB
	:rtype: list[str]
	"""
	#fixme: implement
	return False, False

def may_remove(userA, userB):
	"""
	check whether userA may delete userB's account
	if userA == userB, this returns false if userB is an admin user (admins may not delete themselves)
	:param str userA: username of user who wants to remove a user
	:param str userB: username of user to be removed
	:return: whether the operation is allowed
	:rtype: bool
	"""
	#fixme: implement
	return False