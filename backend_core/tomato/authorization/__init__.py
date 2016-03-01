from ..lib.userflags import Flags
from info import UserInfo, TopologyInfo, SiteInfo, HostInfo
from ..lib.topology_role import Role
from ..lib.cache import cached

class PermissionChecker(UserInfo):
	__slots__ = ()
	def __init__(self, username):
		super(PermissionChecker, self).__init__(username)



	# users

	def may_list_all_users(self):
		"""
		check whether this user may list all users
		:param str organization: name of the organization
		:return: whether this user may list all users
		:rtype: bool
		"""
		# only global admins may do this.
		return Flags.GlobalAdmin in self.get_flags()

	def may_list_organization_users(self, organization):
		"""
		check whether this user may list all users of this organization
		:param str organization: name of the organization
		:return: whether this user may list all users of the organization
		:rtype: bool
		"""
		# global admins and admins of the respective organization may do this.
		if Flags.GlobalAdmin in self.get_flags():
			return True
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == organization:
			return True
		return False

	def info_visible_keys(self, userB):
		"""
		return a list of keys that this user may see if calling info() of userB, or listing all users
		:param UserInfo userB: user to be shown
		:return: keys of user_info() which this user may see
		:rtype: list(str)
		"""
		res = {'name', 'origin', 'id', 'realname'}  # needed for everyone to add a user to a topology.
		if self.get_username() == userB.get_username():
			res.update(['email', 'flags', 'organization', 'quota', 'client_data', 'last_login', 'password_hash'])
		if Flags.GlobalAdmin in self.get_flags() or \
				Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			res.update(['email', 'flags', 'organization', 'quota', 'notification_count', 'client_data', 'last_login', 'password_hash'])
		return res

	def modify_user_allowed_keys(self, userB):
		"""
		return a list of key this user may modify in userB
		note that although flags is always included here, only some flags may be changeble;
		see modify_allowed_flags for more details.

		:param UserInfo userB: user to be modified
		:return: list of keys to be modified
		:rtype: list(str)
		"""
		result = {"flags"}
		if userB.get_username() == self.get_username():
			result.update(("realname", "email", "password"))
			if Flags.GlobalAdmin in self.get_flags():
				result.add("organization")
		else:
			if Flags.GlobalAdmin in self.get_flags():
				result.update(["realname", "email", "organization"])
			if Flags.OrgaAdmin in self.get_flags() and self.info['organization'] == userB.get_organization():
				result.update(["realname", "email"])
		return result

	def modify_user_allowed_flags(self, userB):
		"""
		return a list of flags this user may modify of userB.
		:param UserInfo userB: user to be modified
		:return: flags which this user may modify
		:rtype: bool
		"""
		result = set()
		is_self = userB.get_username() == self.get_username()

		# every user may change their own email settings
		if is_self:
			result.add(Flags.NoMails)

		# all global flags, and OrgaAdmin flag
		if Flags.GlobalAdmin in self.get_flags():
			if not is_self:
				result.add(Flags.GlobalAdmin)  # may not remove own admin privileges
			result.update([
						Flags.GlobalToplOwner,
						Flags.GlobalToplManager,
						Flags.GlobalToplUser,
						Flags.GlobalAdminContact,
						Flags.OrgaAdmin,
						Flags.GlobalHostManager,
						Flags.GlobalHostContact,
						Flags.Debug,
						Flags.ErrorNotify
						])

		# all flags except global flags.
		if Flags.GlobalAdmin in self.get_flags() or \
				(Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization()):
			if not is_self:
				result.add(Flags.OrgaAdmin)  # may not remove own admin privileges. if GlobalAdmin, this has been added before.
			result.update([
						Flags.OrgaAdmin,
						Flags.OrgaToplOwner,
						Flags.OrgaToplManager,
						Flags.OrgaToplUser,
						Flags.OrgaAdminContact,
						Flags.OrgaHostManager,
						Flags.OrgaHostContact,
						Flags.NoTopologyCreate,
						Flags.OverQuota,
						Flags.RestrictedProfiles,
						Flags.RestrictedTemplates,
						Flags.RestrictedNetworks,
						Flags.NewAccount,
						Flags.NoMails
						])
		return result

	def may_reset_password_of_user(self, userB):
		"""
		check whether this user may reset the password for userB.
		:param UserInfo userB: user whose password is to be resetted.
		:return: whether this user may reset B's password
		:rtype: bool
		"""
		if userB.get_username() == self.get_username():
			return True
		if Flags.GlobalAdmin in self.get_flags():
			return True
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			return True
		return False

	def may_delete_user(self, userB):
		"""
		check whether this user may delete userB
		:param UserInfo userB: user to be deleted
		:return: whether this user may delete userB
		:rtype: bool
		"""
		if userB.get_username() == self.get_username():
			if Flags.GlobalAdmin in self.get_flags():  # admins may not delete themselves
				return False
			return True
		if Flags.GlobalAdmin in self.get_flags():
			return True
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			if Flags.GlobalAdmin in userB.get_flags():
				return False  # orgaAdmin may not delete globalAdmin
			return True
		return False

	def may_broadcast_messages(self, organization=None):
		"""
		check whether this user may broadcast messages
		:param None or str organization: if None, check whether broadcast to all is allowed. otherwise, check for this organization.
		:return: whether the user may broadcast messages to the given organization or all
		:rtype: bool
		"""
		flags = self.get_flags()
		if Flags.GlobalAdmin in flags or Flags.GlobalHostManager in flags:
			return True
		if (Flags.OrgaAdmin in flags or Flags.OrgaHostManager in flags) and self.get_organization() == organization:
			return True
		return False

	def may_send_message_to_user(self, userB):
		"""
		check whether this user may send a message to userB
		:param UserInfo userB: receiver of the message
		:return: whether this user may send a message to userB
		:rtype: bool
		"""
		if userB.get_username() == self.get_username():
			return True
		if Flags.GlobalAdmin in self.get_flags():
			return True
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			return True
		return False





	# organizations

	def may_create_organizations(self):
		"""
		check whether this user may create an organization
		:return: whether this user may create an organization
		:rtype: bool
		"""
		return (Flags.GlobalHostManager in self.get_flags()) or (Flags.GlobalAdmin in self.get_flags())

	def may_modify_organization(self, organization):
		"""
		check whether this user may modify this organization
		:param str organization: organization to be modified
		:return: whether this user may modify this organization
		:rtype: bool
		"""
		if Flags.GlobalAdmin in self.get_flags() or Flags.GlobalHostManager in self.get_flags():
			return True
		if (Flags.OrgaAdmin in self.get_flags() or Flags.OrgaHostManager in self.get_flags()) and self.get_organization() == organization:
			return True
		return False

	def may_delete_organization(self, organization):
		"""
		check whether this user may delete this organization
		:param str organization: organization to be deleted
		:return: whether this user may delete this organization
		:rtype: bool
		"""
		if organization == self.get_organization():
			return False  # you may not delete your own organization
		return Flags.GlobalAdmin in self.get_flags() or Flags.GlobalHostManager in self.get_flags()



	# sites

	def _is_hostmanager_for_organization(self, organization):
		"""
		check whether this user is hostmanager for the given organization
		:param str organization: target organization's name
		:return: whether this user is hostmanager for the given organization
		:rtype: bool
		"""
		if Flags.GlobalHostManager in self.get_flags():
			return True
		if Flags.OrgaHostManager in self.get_flags() and organization == self.get_organization():
			return True
		return False

	def may_create_sites(self, organization):
		"""
		check whether this user may create sites for this organization
		:param str organization: target site's organization
		:return: whether this user may create a site for this organization
		:rtype: bool
		"""
		return self._is_hostmanager_for_organization(organization)

	def may_modify_site(self, site_info):
		"""
		check whether this user may modify this site
		:param SiteInfo site_info: target site
		:return: whether this user may modify this site
		:rtype: bool
		"""
		return self._is_hostmanager_for_organization(site_info.get_organization())

	def may_delete_site(self, site_info):
		"""
		check whether this user may delete this site
		:param SiteInfo site_info: target site
		:return: whether this user may delete this site
		:rtype: bool
		"""
		return self._is_hostmanager_for_organization(site_info.get_organization())




	# hosts

	def may_create_hosts(self, site_info):
		"""
		check whether this user may create hosts for this site
		:param SiteInfo site_info: target hosts's site
		:return: whether this user may create a hosts for this site
		:rtype: bool
		"""
		return self._is_hostmanager_for_organization(site_info.get_organization())

	def may_modify_host(self, host_info):
		"""
		check whether this user may modify this host
		:param HostInfo host_info: target host
		:return: whether this user may modify this host
		:rtype: bool
		"""
		return self._is_hostmanager_for_organization(host_info.get_organization())

	def may_delete_host(self, host_info):
		"""
		check whether this user may delete this host
		:param HostInfo host_info: target host
		:return: whether this user may delete this host
		:rtype: bool
		"""
		return self._is_hostmanager_for_organization(host_info.get_organization())

	def may_list_host_users(self, host_info):
		"""
		check whether this user may list users of this host
		:param HostInfo host_info: target host
		:return: whether this user list users of this host
		:rtype: bool
		"""
		return self._is_hostmanager_for_organization(host_info.get_organization())






	# topologies

	def _has_topology_role(self, topology_info, role):
		"""
		check whether the user has a given role on the topology.
		return True if the user has a higher role.
		this also checks for user permission flags like GlobalToplManager.

		:param TopologyInfo topology_info: target topology info
		:param str role: target role
		:return: whether this user has this role on this topology
		:rtype: bool
		"""
		# first, try to resolve this without topology information
		perm_global, perm_orga = Flags.getMaxTopologyFlags(self.get_flags())
		if Role.leq(role, perm_global):
			return True

		if topology_info.user_has_role(self.get_username(), role):
			return True
		if Role.leq(role, perm_orga):  # user has role in organization
			if topology_info.organization_has_role(self.get_organization(), role):  # organization has role on topology
				return True
		return False

	def may_create_topologies(self):
		"""
		check whether this user may create topologies.
		:return: whether the user may create topologies.
		:rtype: bool
		"""
		return Flags.NoTopologyCreate not in self.get_flags()

	def may_view_topology(self, topology_info):
		"""
		check whether this user may view this topology.
		:param TopologyInfo topology_info: target topology
		:return: whether this user may view this topology.
		:rtype: bool
		"""
		return self._has_topology_role(topology_info, Role.user)

	def may_remove_topology(self, topology_info):
		"""
		check whether this user may remove this topology.
		:param TopologyInfo topology_info: target topology
		:return: whether this user may remove this topology.
		:rtype: bool
		"""
		return self._has_topology_role(topology_info, Role.owner)

	def may_modify_topology(self, topology_info):
		"""
		check whether this user may modify this topology.
		:param TopologyInfo topology_info: target topology
		:return: whether this user may modify this topology.
		:rtype: bool
		"""
		return self._has_topology_role(topology_info, Role.owner)

	def may_run_topology_actions(self, topology_info):
		"""
		check whether this user may run actions on this topology.
		:param TopologyInfo topology_info: target topology
		:return: whether this user may run actions on this topology.
		:rtype: bool
		"""
		return self._has_topology_role(topology_info, Role.manager)

	def may_list_all_topologies(self):
		"""
		check whether this user may see info of all topologies.
		:return: whether this user may see info of all topologies.
		:rtype: bool
		"""
		return Flags.GlobalToplUser in self.get_flags()

	def may_list_organization_topologies(self, organization):
		"""
		check whether this user may see info of all topologies of this organization.
		:param str organization: name of target organization
		:return: whether this user may see info of all topologies of this organization.
		:rtype: bool
		"""
		return (Flags.OrgaToplUser in self.get_flags()) and (self.get_organization() == organization)

	def may_grant_permission_for_topologies(self, topology_info, role, username):
		"""
		check whether this user may grant another user this permission on this topology.
		:param str role: target role as in auth.permissions.Role
		:param TopologyInfo topology_info: target topology
		:param str username: target user
		:return: whether this user may grant this permission on this topology.
		:rtype: bool
		"""
		return self._has_topology_role(topology_info, role) and not (username == self.get_username())










@cached(60)
def get_permission_checker(username):
	"""
	get PermissionChecker for this username
	:param str username: username of user
	:return: PermissionChecker object for corresponding user
	:rtype: PermissionChecker
	"""
	return PermissionChecker(username=username)

def get_user_info(username):
	"""
	return UserInfo object for this username
	:param str username: username of user
	:return: PermissionChecker object for corresponding user
	:rtype: PermissionChecker
	"""
	return get_permission_checker(username)

@cached(3600)
def get_topology_info(topology_id):
	"""
	return TopologyInfo object for the respective topology
	:param topology_id: id of topology
	:return: TopologyInfo object
	:rtype: TopologyInfo
	"""
	return TopologyInfo(topology_id)

@cached(3600)
def get_site_info(site_name):
	"""
	return SiteInfo object for the respective site
	:param str site_name: name of the target site
	:return: SiteInfo object
	:rtype: SiteInfo
	"""
	return SiteInfo(site_name)

@cached(3600)
def get_host_info(host_name):
	"""
	return HostInfo object for the respective host
	:param str host_name: name of the target host
	:return: HostInfo object
	:rtype: HostInfo
	"""
	return HostInfo(host_name)
