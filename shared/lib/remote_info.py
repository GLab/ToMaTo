from error import InternalError
from service import get_backend_users_proxy, get_backend_core_proxy
from cache import cached
import topology_role

class ExistenceCheck(object):
	"""
	An object that can check the existence of a remote object.
	Abstract class that should be implemented regarding a certain remote class.
	Caches information in its fields about the existence.
	An instance of this is always linked to an remote object.

	You should override _check_exists(self) when creating a subclass.
	"""
	__slots__ = ("_exists",)

	def __init__(self):
		self._exists = None

	def invalidate_exists(self):
		"""
		call this if the existence of this is no longer guaranteed.
		remove cached info about existence.
		:return: None
		"""
		self._exists = None

	def set_exists(self, exists):
		"""
		use this if you certainly know about the existence about this.
		:param bool exists: whether the object exists or not
		:return: None
		"""
		self._exists = exists

	def exists(self):
		"""
		check whether this exists. This information probably cached locally.
		:return: whether this object exists remotely.
		:rtype: bool
		"""
		if self._exists is None:
			self._exists = self._check_exists()
		return self._exists

	def _check_exists(self):
		"""
		check whether this object exists remotely. Do not modify any fields here!
		:return: whether it exists
		:rtype: bool
		"""
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden", data={'function': '%s.exists' % repr(self.__class__)})

class InfoObj(ExistenceCheck):
	"""
	An Existencecheck object which can aditionally hold cached info about the remote object.
	Supports info, modify and remove methods.

	When creating a subclass, override _fetch_info, _modify, _remove
	"""
	__slots__ = ("_info",)

	def __init__(self):
		super(InfoObj, self).__init__()
		self._info = None

	def invalidate_info(self):
		"""
		Call this if server info is known to have changed.
		remove info cache. Does not change exists knowledge.
		:return:
		"""
		self._info = None

	def _fetch_info(self, fetch=False):
		"""
		fetch info from server. Do not modify any fields here!
		:param fetch: if true, force the server to update remote info.
		:return: server info as fetched from server
		:rtype: dict
		"""
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden", data={'function': '%s._fetch_info' % repr(self.__class__)})

	def _modify(self, attrs):
		"""
		modify data on server. return object info. Do not modify any fields here!
		You should invalidate info of other objects if needed.
		:param dict attrs: params for modification.
		:return: server info as fetched from server (usually returned by ____modify)
		:rtype: dict
		"""
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden",
												data={'function': '%s._modify' % repr(self.__class__)})

	def _remove(self):
		"""
		remove the object from the server. Do not modify any fields here!
		You should invalidate info of other objects if needed.
		:return: None
		"""
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden",
												data={'function': '%s._remove' % repr(self.__class__)})

	def set_exists(self, exists):
		super(InfoObj, self).set_exists(exists)
		self.invalidate_info()

	def _check_exists(self):
		if self._info is not None:
			return True
		try:
			self.info()
			return True
		except:
			return False

	def info(self, fetch=False, update=False):
		"""
		get info, probably cached locally.. load from other services if needed.
		:param bool fetch: force local refresh. If supported, let _fetch_info to tell the server to force updates remotely.
		:param bool update: force local refresh.
		:return: object info
		:rtype: dict
		"""
		if fetch or update or (self._info is None):
			self._info = self._fetch_info(fetch)
			self.set_exists(True)  # otherwise, fetch_data would have thrown an error
		return self._info

	def modify(self, attrs):
		"""
		call corresponding modify function. update info.
		:param dict attrs: params for object modification
		:return: object info
		:rtype: dict
		"""
		self._info = self._modify(attrs)
		return self._info

	def remove(self):
		"""
		remove the object. delete cache.
		:return: None
		"""
		self._remove()
		self.set_exists(False)


class ActionObj(InfoObj):
	"""
	An InfoObj that supports actions.

	When creating a subclass, override _fetch_info, _modify, _remove, _action.
	"""

	__slots__ = ()

	def __init__(self):
		super(ActionObj, self).__init__()

	def _action(self, action, params):
		"""
		run an action. Do not modify any fields here!
		Usually, afterwards, every knowledge about this object will be invalidated.
		  If you do not wish this, override _after_action.
		:param str action: action name
		:param str params: action params
		:return: action return value
		"""
		raise InternalError(code=InternalError.UNKNOWN, message="this function should have been overridden",
												data={'function': '%s._action' % repr(self.__class__)})

	def _after_action(self, action, params):
		"""
		does not need to be overwritten.
		Called after a successful action. should invalidate all information which may have changed during the action.

		:param str action: action that has been run
		:param str params: action params of this action.
		:return: None
		"""
		self.invalidate_info()
		self.invalidate_exists()

	def action(self, action, params):
		"""
		run the action. Afterwards, all information will be invalidated.
		:param action:
		:param params:
		:return:
		"""
		res = self._action(action, params)
		self._after_action(action, params)
		return res



class UserInfo(InfoObj):
	__slots__ = ("name",)

	def __init__(self, username):
		super(UserInfo, self).__init__()
		self.name = username

	def _fetch_info(self, fetch=False):
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

	def _modify(self, attrs):
		orga = None
		if ('organization' in attrs) and (self.get_organization_name() != attrs['organization']):
			orga = self.get_organization_name()
		res = get_backend_users_proxy().user_modify(self.name, attrs)
		if orga is not None:
			get_organization_info(orga).invalidate_info()
			get_organization_info(attrs['organization']).invalidate_info()
		return res

	def _remove(self):
		orga = self.get_organization_name()
		get_backend_users_proxy().user_remove(self.name)
		get_organization_info(orga).invalidate_info()


class OrganizationInfo(InfoObj):
	__slots__ = ("name",)

	def __init__(self, organization_name):
		super(OrganizationInfo, self).__init__()
		self.name = organization_name

	def _fetch_info(self, fetch=False):
		return get_backend_users_proxy().organization_info(self.name)

	def get_organization_name(self):
		return self.get_organization_name()

	def _check_exists(self):
		if self._info is not None:
			return True
		return get_backend_users_proxy().organization_exists(self.name)

	def _modify(self, attrs):
		return get_backend_users_proxy().organization_modify(self.name, attrs)

	def _remove(self):
		get_backend_users_proxy().organization_remove(self.name)


class TopologyInfo(ActionObj):
	__slots__ = ("topology_id", )

	def __init__(self, topology_id):
		super(TopologyInfo, self).__init__()
		self.topology_id = topology_id

	def _fetch_info(self, fetch=False):
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
		user_role = self.info()['permissions'][username]
		return topology_role.Role.leq(role,user_role)

	def organization_has_role(self, organization, role):
		"""
		check whether the organization has the given role.

		:param str organization: target organization name
		:param str role: maximum role as in auth.permissions.Role
		:return: the role
		:rtype: bool
		"""
		user_list = []
		for user, user_role in self.info()['permissions'].iteritems():
			if topology_role.Role.leq(role,user_role):
				user_list.append(user)

		organizations_with_role = get_backend_users_proxy().organization_list(user_list)

		return (organization in organizations_with_role)

	def set_permission(self, user, role):
		"""
		set the permission of a user
		:param str user: username of target user
		:param str role: role as in topology_role
		"""
		res = get_backend_core_proxy().topology_set_permission(id, user, role)  # fixme: do this in TopologyInfo
		if self._info is not None:
			self._info['permissions'][user] = role
		return res

	def get_id(self):
		"""
		return the topology id of this toppology
		:return:
		"""
		return self.topology_id

	def _modify(self, attrs):
		return get_backend_core_proxy().topology_modify(self.topology_id, attrs)

	def _remove(self):
		elems = self.info()['elements']
		conns = self.info()['connections']
		get_backend_core_proxy().topology_remove(self.topology_id)
		for e in elems:
			get_element_info(e).set_exists(False)
		for c in conns:
			get_connection_info(c).set_exists(False)

	def _action(self, action, params):
		elems = self.info()['elements']
		conns = self.info()['connections']
		res = get_backend_core_proxy().topology_action(self.topology_id, action, params)
		for e in elems:
			get_element_info(e).invalidate_info()
			get_element_info(e).invalidate_exists()
		for c in conns:
			get_connection_info(c).invalidate_info()
			get_connection_info(c).invalidate_exists()
		return res








class SiteInfo(InfoObj):
	__slots__ = ("name",)

	def invalidate_exists(self):
		get_organization_info(self.get_organization_name()).invalidate_info()
		super(SiteInfo, self).invalidate_exists()

	def invalidate_info(self):
		get_organization_info(self.get_organization_name()).invalidate_info()
		super(SiteInfo, self).invalidate_info()

	def set_exists(self, exists):
		get_organization_info(self.get_organization_name()).invalidate_info()
		super(SiteInfo, self).set_exists(exists)

	def __init__(self, site_name):
		super(SiteInfo, self).__init__()
		self.name = site_name

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().site_info(self.name)

	def _modify(self, attrs):
		orga = None
		if ('organization' in attrs) and (self.get_organization_name() != attrs['organization']):
			orga = self.get_organization_name()
		res = get_backend_core_proxy().site_modify(self.name, attrs)
		if orga is not None:
			get_organization_info(orga).invalidate_info()
			get_organization_info(attrs['organization']).invalidate_info()
		return res

	def _remove(self):
		orga = self.get_organization_name()
		get_backend_core_proxy().site_remove(self.name)
		get_organization_info(orga).invalidate_info()

	def get_organization_name(self):
		return self.info()['organization']




class HostInfo(InfoObj):
	__slots__ = ("name",)

	def __init__(self, host_name):
		super(HostInfo, self).__init__()
		self.name = host_name

	def invalidate_exists(self):
		get_site_info(self.get_site_name()).invalidate_info()
		super(HostInfo, self).invalidate_exists()

	def invalidate_info(self):
		get_site_info(self.get_site_name()).invalidate_info()
		super(HostInfo, self).invalidate_info()

	def set_exists(self, exists):
		get_site_info(self.get_site_name()).invalidate_info()
		super(HostInfo, self).set_exists(exists)

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().host_info(self.name)

	def _modify(self, attrs):
		site = None
		if ('site' in attrs) and (self.get_site_name() != attrs['site']):
			site = self.get_site_name()
		res = get_backend_core_proxy().host_modify(self.name, attrs)
		if site is not None:
			get_site_info(site).invalidate_info()
			get_site_info(attrs['site']).invalidate_info()
		return res

	def _remove(self):
		site = self.get_site_name()
		get_backend_core_proxy().host_remove(self.name)
		get_site_info(site).invalidate_info()

	def get_site_name(self):
		return self.info()['site']

	def get_organization_name(self):
		return self.info()['organization']

	def get_clock_offset(self):
		return self.info()['host_info']['time_diff']

	def get_dumps(self, after):
		return get_backend_core_proxy().host_dump_list(self.name, after)


class ElementInfo(ActionObj):
	__slots__ = ("eid",)

	def _after_action(self, action, params):
		super(ElementInfo, self)._after_action(action, params)
		self.get_topology_info().invalidate_info()

	def __init__(self, element_id):
		super(ElementInfo, self).__init__()
		self.eid = element_id

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().element_info(self.eid, fetch=fetch)

	def _modify(self, attrs):
		return get_backend_core_proxy().element_modify(self.eid, attrs)

	def _remove(self):
		get_backend_core_proxy().element_remove(self.eid)
		self.get_topology_info().invalidate_info()

	def _action(self, action, params):
		self.get_topology_info().invalidate_info()
		return get_backend_core_proxy().element_action(self.eid, action, params)

	def get_topology_info(self):
		return get_topology_info(self.info()['topology'])

	def get_type(self):
		return self.info()['type']

class ConnectionInfo(ActionObj):
	__slots__ = ("cid",)

	def _after_action(self, action, params):
		super(ConnectionInfo, self)._after_action(action, params)
		self.get_topology_info().invalidate_info()

	def __init__(self, connection_id):
		super(ConnectionInfo, self).__init__()
		self.cid = connection_id

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().element_info(self.eid, fetch=fetch)

	def _modify(self, attrs):
		return get_backend_core_proxy().connection_modify(self.eid, attrs)

	def _remove(self):
		get_backend_core_proxy().connection_remove(self.eid)
		self.get_topology_info().invalidate_info()

	def _action(self, action, params):
		self.get_topology_info().invalidate_info()
		return get_backend_core_proxy().connection_action(self.eid, action, params)

	def get_topology_info(self):
		return get_topology_info(self.info()['topology'])

class TemplateInfo(InfoObj):
	__slots__ = ("template_id")

	def __init__(self, template_id):
		super(TemplateInfo, self).__init__()
		self.template_id = template_id

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().template_info(self.template_id)

	def _modify(self, attrs):
		return get_backend_core_proxy().template_modify(self.template_id, attrs)

	def _remove(self):
		get_backend_core_proxy().template_remove(self.template_id)

	def is_restricted(self):
		return self.info()['restricted']

class ProfileInfo(InfoObj):
	__slots__ = ("profile_id")

	def __init__(self, profile_id):
		super(ProfileInfo, self).__init__()
		self.profile_id = profile_id

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().profile_info(self.profile_id)

	def _modify(self, attrs):
		return get_backend_core_proxy().profile_modify(self.profile_id, attrs)

	def _remove(self):
		get_backend_core_proxy().profile_remove(self.profile_id)

	def is_restricted(self):
		return self.info()['restricted']

class NetworkInfo(InfoObj):
	__slots__ = ("kind",)

	def __init__(self, kind):
		super(NetworkInfo, self).__init__()
		self.kind = kind

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().network_info(self.kind)

	def _modify(self, attrs):
		return get_backend_core_proxy().network_modify(self.kind, attrs)

	def _remove(self):
		get_backend_core_proxy().network_remove(self.kind)

	def is_restricted(self):
		return self.info()['restricted']

class NetworkInstanceInfo(InfoObj):
	__slots__ = ("niid",)

	def __init__(self, network_instance_id):
		super(NetworkInstanceInfo, self).__init__()
		self.niid = network_instance_id

	def _fetch_info(self, fetch=False):
		return get_backend_core_proxy().network_instance_info(self.niid)

	def _modify(self, attrs):
		return get_backend_core_proxy().network_instance_modify(self.niid, attrs)

	def _remove(self):
		get_backend_core_proxy().network_instance_remove(self.niid)





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

@cached(60)
def get_network_instance_info(network_instance_id):
	"""
	return NetworkInstanceInfo object for the respective network instance
	:param str network_instance_id: id of the target network instance
	:return: NetworkInstanceInfo object
	:rtype: NetworkInstanceInfo
	"""
	return NetworkInstanceInfo(network_instance_id)
