from ..lib.remote_info import UserInfo, InfoObj
from permission_checker import PermissionChecker

class PseudoUser(UserInfo):
	"""
	UserInfo-like object for non-existing users.
	"""
	__slots__ = ("organization",)

	def __init__(self, username, organization):
		super(PseudoUser, self).__init__(username)
		self.organization = organization

	def _fetch_info(self, fetch=False):
		return {
			'organization': self.organization,
			'name': self.name
		}

	def _modify(self, attrs):
		return InfoObj._modify(self, attrs)

	def _remove(self):
		return InfoObj._remove(self)





def login(username, password):
	"""
	check credentials. on success, return permission checker object
	:param username: provided username
	:param password: provided password
	:return: PermissionChecker object belonging to the user
	:rtype: PermissionChecker
	"""
	user_info = get_permission_checker(username)
	if user_info.login(password):
		return user_info
	else:
		return None


def get_permission_checker(username):
	"""
	get PermissionChecker for this username
	:param str username: username of user
	:return: PermissionChecker object for corresponding user
	:rtype: PermissionChecker
	"""
	return PermissionChecker(username=username)

def get_pseudo_user_info(username, organization):
	"""
	return UserInfo object for a non-existing user
	:param str username: username of user
	:return: PermissionChecker object for corresponding user
	:rtype: PermissionChecker
	"""
	return PseudoUser(username, organization)
