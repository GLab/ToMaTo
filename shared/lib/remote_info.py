from error import InternalError
from service import get_backend_users_proxy
from cache import cached

class ExistenceCheck(object):
	__slots__ = ("_exists",)

	def __init__(self):
		self._exists = None

	def invalidate_exists(self):
		self._exists = None

	def set_exists(self, exists):
		self._exists = exists

	def exists(self):
		if self._exists is None:
			self._exists = self._check_exists()
		return self._exists

	def _check_exists(self):
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden", data={'function': '%s.exists' % repr(self.__class__)})

class InfoObj(ExistenceCheck):
	__slots__ = ("_info")

	def __init__(self):
		super(InfoObj, self).__init__()
		self._info = None

	def invalidate_info(self):
		self._info = None
		self.invalidate_exists()

	def _fetch_data(self):
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden", data={'function': '%s._fetch_data' % repr(self.__class__)})

	def info(self):
		if self._info is None:
			self._info = self._fetch_data()
			self.set_exists(True)  # otherwise, fetch_data would have thrown an error
		return self._info


class UserInfo(InfoObj):
	__slots__ = ("name",)

	def __init__(self, username):
		super(UserInfo, self).__init__()
		self.name = username

	def _fetch_data(self):
		return get_backend_users_proxy().user_info(self.name)

	def get_username(self):
		return self.name

	def get_flags(self):
		return self.info()['flags']

	def get_organization_name(self):
		return self.info()['organization']

	def _check_exists(self):
		if self._info is not None:
			return True
		return get_backend_users_proxy().user_exists(self.name)


class OrganizationInfo(InfoObj):
	__slots__ = ("name",)

	def __init__(self, organization_name):
		super(OrganizationInfo, self).__init__()
		self.name = organization_name

	def _fetch_data(self):
		return get_backend_users_proxy().organization_info(self.name)

	def get_organization_name(self):
		return self.get_organization_name()

	def _check_exists(self):
		if self._info is not None:
			return True
		return get_backend_users_proxy().organization_exists(self.name)


@cached(60)
def get_user_info(username):
	"""
	return UserInfo object for this username
	:param str username: username of user
	:return: UserInfo object for corresponding user
	:rtype: UserInfo
	"""
	return UserInfo(username)

@cached(60)
def get_organization_info(organization_name):
	"""
	return OrganizationInfo object for the respective organization
	:param str organization_name: name of the target organization
	:return: OrganizationInfo object
	:rtype: OrganizationInfo
	"""
	return OrganizationInfo(organization_name)
