from ..lib.error import UserError

from .remote_info import ExistenceCheck

from ..topology import Topology
from ..elements import Element
from ..connections import Connection
from ..host.site import Site
from ..host import Host
from ..resources.template import Template
from ..resources.profile import Profile
from ..resources.network import Network









class TopologyInfo(ExistenceCheck):
	"""
	:type topology: Topology
	"""
	__slots__ = ("topology", "topology_id")

	def __init__(self, topology_id):
		self.topology = Topology.get(topology_id)
		UserError.check(self.topology, code=UserError.ENTITY_DOES_NOT_EXIST, message="Topology with that id does not exist", data={"topology_id": topology_id})
		self.topology_id = topology_id

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

	def organization_has_role(self, organization, role):
		"""
		check whether the organization has the given role.

		:param str organization: target organization name
		:param str role: maximum role as in auth.permissions.Role
		:return: the role
		:rtype: bool
		"""
		return self.topology.organization_has_role(organization, role)

	def get_id(self):
		"""
		return the topology id of this toppology
		:return:
		"""
		return self.topology_id

	def _check_exists(self):
		# __init__ would throw an error if it didn't exist...
		return True


class SiteInfo(ExistenceCheck):
	__slots__ = ("site",)

	def __init__(self, site_name):
		super(SiteInfo, self).__init__()
		self.site = Site.objects.get(site_name)
		UserError.check(self.site, code=UserError.ENTITY_DOES_NOT_EXIST, message="Site with that name does not exist", data={"site_name": site_name})

	def get_organization_name(self):
		return self.site.organization

	def _check_exists(self):
		# __init__ would throw an error if it didn't exist...
		return True

class HostInfo(ExistenceCheck):
	__slots__ = ("host",)

	def __init__(self, host_name):
		super(HostInfo, self).__init__()
		self.host = Host.objects.get(host_name)
		UserError.check(self.host, code=UserError.ENTITY_DOES_NOT_EXIST, message="Host with that name does not exist", data={"host_name": host_name})

	def get_organization_name(self):
		return self.host.site.organization

	def _check_exists(self):
		# __init__ would throw an error if it didn't exist...
		return True

class ElementInfo(ExistenceCheck):
	__slots__ = ("element",)

	def __init__(self, element_id):
		super(ElementInfo, self).__init__()
		self.element = Element.get(element_id)
		UserError.check(self.element, code=UserError.ENTITY_DOES_NOT_EXIST, message="Element with that id does not exist", data={"element_id": element_id})

	def get_topology_info(self):
		return get_topology_info(self.element.topology.id)

	def _check_exists(self):
		# __init__ would throw an error if it didn't exist...
		return True

	def get_type(self):
		return self.element.type

class ConnectionInfo(ExistenceCheck):
	__slots__ = ("connection",)

	def __init__(self, connection_id):
		super(ConnectionInfo, self).__init__()
		self.connection = Connection.get(connection_id)
		UserError.check(self.connection, code=UserError.ENTITY_DOES_NOT_EXIST, message="Connection with that id does not exist", data={"connection_id": connection_id})

	def get_topology_info(self):
		return get_topology_info(self.connection.topology.id)

	def _check_exists(self):
		# __init__ would throw an error if it didn't exist...
		return True

class TemplateInfo(object):
	__slots__ = ("template",)

	def __init__(self, tech, name):
		super(TemplateInfo, self).__init__()
		self.template = Template.get(tech, name)
		UserError.check(self.template, code=UserError.ENTITY_DOES_NOT_EXIST, message="Template with that name and tech does not exist", data={"name": name, "tech": tech})

	def is_restricted(self):
		return self.temlate.restricted

class ProfileInfo(object):
	__slots__ = ("profile",)

	def __init__(self, tech, name):
		super(ProfileInfo, self).__init__()
		self.profile = Profile.get(tech, name)
		UserError.check(self.profile, code=UserError.ENTITY_DOES_NOT_EXIST, message="Profile with that name and tech does not exist", data={"name": name, "tech": tech})

	def is_restricted(self):
		return self.profile.restricted

class NetworkInfo(object):
	__slots__ = ("network",)

	def __init__(self, kind):
		super(NetworkInfo, self).__init__()
		self.network = Network.get(kind)
		UserError.check(self.network, code=UserError.ENTITY_DOES_NOT_EXIST, message="Network of that kind does not exist", data={"kind": kind})

	def is_restricted(self):
		return self.network.restricted





def get_connection_info(connection_id):
	"""
	return ConnectionInfo object for the respective topology
	:param connection_id: id of connection
	:return: ConnectionInfo object
	:rtype: ConnectionInfo
	"""
	return ConnectionInfo(connection_id)

def get_element_info(element_id):
	"""
	return ElementInfo object for the respective element
	:param element_id: id of element
	:return: ElementInfo object
	:rtype: ElementInfo
	"""
	return ElementInfo(element_id)


def get_topology_info(topology_id):
	"""
	return TopologyInfo object for the respective topology
	:param topology_id: id of topology
	:return: TopologyInfo object
	:rtype: TopologyInfo
	"""
	return TopologyInfo(topology_id)


def get_site_info(site_name):
	"""
	return SiteInfo object for the respective site
	:param str site_name: name of the target site
	:return: SiteInfo object
	:rtype: SiteInfo
	"""
	return SiteInfo(site_name)


def get_host_info(host_name):
	"""
	return HostInfo object for the respective host
	:param str host_name: name of the target host
	:return: HostInfo object
	:rtype: HostInfo
	"""
	return HostInfo(host_name)

def get_template_info(tech, name):
	"""
	return TemplateInfo object for the respective template
	:param str tech: tech of the target template
	:param str name: name of the target template
	:return: TemplateInfo object
	:rtype: TemplateInfo
	"""
	return TemplateInfo(tech, name)

def get_profile_info(tech, name):
	"""
	return ProfileInfo object for the respective profile
	:param str tech: tech of the target profile
	:param str name: name of the target profile
	:return: ProfileInfo object
	:rtype: ProfileInfo
	"""
	return ProfileInfo(tech, name)

def get_network_info(kind):
	"""
	return NetworkInfo object for the respective network
	:param str kind: kind of the target network
	:return: NetworkInfo object
	:rtype: NetworkInfo
	"""
	return NetworkInfo(kind)
