from .. import scheduler
from ..lib.error import InternalError, UserError
from ..lib.service import get_tomato_inner_proxy
from ..lib.settings import Config

from ..topology import Topology
from ..auth.permissions import Role

class InfoObj(object):
	def __init__(self, cache_duration):
		self._cache_duration = cache_duration
		self._info = None

	def invalidate_info(self):
		self._info = None

	def _fetch_data(self):
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden", data={'function': '%s._fetch_data' % repr(self.__class__)})

	def info(self):
		if self._info is None:
			self._info = self._fetch_data()
			scheduler.scheduleOnce(self._cache_duration, self.invalidate_info)
		return self._info




class UserInfo(InfoObj):
	def __init__(self, username):
		super(UserInfo, self).__init__(60)  # fixme: invalidation interval should be configurable
		self.name = username

	def _fetch_data(self):
		return get_tomato_inner_proxy(Config.TOMATO_MODULE_BACKEND_USERS).user_info(self.name)

	def get_username(self):
		return self.name

	def get_flags(self):
		return self.info()['flags']

	def get_organization(self):
		return self.info()['organization']




class TopologyInfo:
	def __init__(self, topology_id):
		self.topology = Topology.get(topology_id)
		UserError.check(self.topology, code=UserError.ENTITY_DOES_NOT_EXIST, message="Topology with that id does not exist", data={"id": id_})

	def hasRole(self, username, role):
		"""
		check if the user 'username' has the role 'role'.
		This ignores user flags like
		:param str username: user to check
		:param str role: role as in auth.permissions.Role
		:return: whether the user has this role (or a higher one)
		:rtype: bool
		"""
		#fixme: implement
		return False

	def listUsers(self, minRole=Role.null):
		"""
		get a list of users that have at least the given role.

		:param str minRole: role as in auth.permissions.Role
		:return: list of usernames satisfying the role
		:rtype: list(str)
		"""
		#fixme: implement
		return False