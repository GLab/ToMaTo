from error import InternalError
from service import get_backend_users_proxy, get_backend_core_proxy
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

	def _check_exists(self):
		if self._info is not None:
			return True
		try:
			self.info()
			return True
		except:
			return False

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


class TopologyInfo(InfoObj):
	"""
	:type topology: Topology
	"""
	__slots__ = ("topology_id", )

	def __init__(self, topology_id):
		super(TopologyInfo, self).__init__()
		self.topology_id = topology_id

	def _fetch_data(self):
		return get_backend_core_proxy().topology_info(self.topology_id)

	def user_has_role(self, username, role):
		"""
		check if the user 'username' has the role 'role'.
		This ignores global or organization-internal permission flags of the given user.
		:param str username: user to check
		:param str role: role as in auth.permissions.Role
		:return: whether the user has this role (or a higher one)
		:rtype: bool
		"""
		return self.topology.user_has_role(username, role)
		# fixme: is broken

	def organization_has_role(self, organization, role):
		"""
		check whether the organization has the given role.

		:param str organization: target organization name
		:param str role: maximum role as in auth.permissions.Role
		:return: the role
		:rtype: bool
		"""
		return self.topology.organization_has_role(organization, role)
		# fixme: is broken

	def get_id(self):
		"""
		return the topology id of this toppology
		:return:
		"""
		return self.topology_id








class SiteInfo(InfoObj):
	__slots__ = ("name",)

	def __init__(self, site_name):
		super(SiteInfo, self).__init__()
		self.name = site_name

	def _fetch_data(self):
		return get_backend_core_proxy().site_info(self.name)

	def get_organization_name(self):
		return self.info()['organization']




class HostInfo(InfoObj):
	__slots__ = ("name",)

	def __init__(self, host_name):
		super(HostInfo, self).__init__()
		self.name = host_name

	def _fetch_data(self):
		return get_backend_core_proxy().host_info(self.name)

	def get_organization_name(self):
		return self.info()['organization']


class ElementInfo(InfoObj):
	__slots__ = ("eid",)

	def __init__(self, element_id):
		super(ElementInfo, self).__init__()
		self.eid = element_id

	def _fetch_data(self):
		return get_backend_core_proxy().element_info(self.eid)

	def get_topology_info(self):
		return get_topology_info(self.info()['topology'])

	def get_type(self):
		return self.info()['type']

class ConnectionInfo(InfoObj):
	__slots__ = ("cid",)

	def __init__(self, connection_id):
		super(ConnectionInfo, self).__init__()
		self.cid = connection_id

	def _fetch_data(self):
		return get_backend_core_proxy().connection_info(self.cid)

	def get_topology_info(self):
		return get_topology_info(self.info()['topology'])

class TemplateInfo(InfoObj):
	__slots__ = ("template_id")

	def __init__(self, template_id):
		super(TemplateInfo, self).__init__()
		self.template_id = template_id

	def _fetch_data(self):
		return get_backend_core_proxy().template_info(self.template_id)

	def is_restricted(self):
		return self.info()['restricted']

class ProfileInfo(InfoObj):
	__slots__ = ("profile_id")

	def __init__(self, profile_id):
		super(ProfileInfo, self).__init__()
		self.profile_id = profile_id

	def _fetch_data(self):
		return get_backend_core_proxy().profile_info(self.profile_id)

	def is_restricted(self):
		return self.info()['restricted']

class NetworkInfo(InfoObj):
	__slots__ = ("kind",)

	def __init__(self, kind):
		super(NetworkInfo, self).__init__()
		self.kind = kind

	def _fetch_data(self):
		return get_backend_core_proxy().network_info(self.kind)

	def is_restricted(self):
		return self.info()['restricted']





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

@cached(60)
def get_topology_info(topology_id):
	"""
	return TopologyInfo object for the respective topology
	:param str topology_id: id of the target topology
	:return: TopologyInfo object
	:rtype: TopologyInfo
	"""
	return TopologyInfo(topology_id)

@cached(60)
def get_site_info(site_name):
	"""
	return SiteInfo object for the respective site
	:param str site_name: name of the target site
	:return: SiteInfo object
	:rtype: SiteInfo
	"""
	return SiteInfo(site_name)

@cached(60)
def get_host_info(host_name):
	"""
	return HostInfo object for the respective host
	:param str host_name: name of the target host
	:return: HostInfo object
	:rtype: HostInfo
	"""
	return HostInfo(host_name)

@cached(60)
def get_element_info(element_id):
	"""
	return ElementInfo object for the respective element
	:param str element_id: id of the target element
	:return: ElementInfo object
	:rtype: ElementInfo
	"""
	return ElementInfo(element_id)

@cached(60)
def get_connection_info(connection_id):
	"""
	return ConnectionInfo object for the respective connection
	:param str connection_id: id of the target connection
	:return: ConnectionInfo object
	:rtype: ConnectionInfo
	"""
	return ConnectionInfo(connection_id)

@cached(60)
def get_template_info(template_id):
	"""
	return TemplateInfo object for the respective template
	:param str template_id: id of the target template
	:return: TemplateInfo object
	:rtype: TemplateInfo
	"""
	return TemplateInfo(template_id)

@cached(60)
def get_profile_info(profile_id):
	"""
	return ProfileInfo object for the respective profile
	:param str profile_id: id of the target profile
	:return: ProfileInfo object
	:rtype: ProfileInfo
	"""
	return ProfileInfo(profile_id)


@cached(60)
def get_template_info_by_techname(tech, name):
	"""
	return TemplateInfo object for the respective template
	:param str tech: tech of the target template
	:param str name: name of the target template
	:return: TemplateInfo object
	:rtype: TemplateInfo
	"""
	template_id = get_backend_core_proxy().template_id(tech, name)
	return get_template_info(template_id)


@cached(60)
def get_profile_info_by_techname(tech, name):
	"""
	return ProfileInfo object for the respective profile
	:param str tech: tech of the target profile
	:param str name: name of the target profile
	:return: ProfileInfo object
	:rtype: ProfileInfo
	"""
	profile_id = get_backend_core_proxy().profile_id(tech, name)
	return get_profile_info(profile_id)


@cached(60)
def get_network_info(kind):
	"""
	return NetworkInfo object for the respective network
	:param str kind: id of the target network
	:return: NetworkInfo object
	:rtype: NetworkInfo
	"""
	return NetworkInfo(kind)
