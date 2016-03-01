from ..lib.userflags import Flags
from info import UserInfo, TopologyInfo, SiteInfo, HostInfo
from ..lib.topology_role import Role
from ..lib.cache import cached
from ..lib.error import UserError


def auth_check(condition, message):
	UserError.check(condition, code=UserError.DENIED, message=message)

def auth_fail(message):
	auth_check(False, message)


class PermissionChecker(UserInfo):
	__slots__ = ()
	def __init__(self, username):
		super(PermissionChecker, self).__init__(username)



	# users

	def check_may_list_all_users(self):
		"""
		check whether this user may list all users
		:param str organization: name of the organization
		"""
		# only global admins may do this.
		auth_check(Flags.GlobalAdmin not in self.get_flags(), "operation requires global admin permission.")

	def check_may_list_organization_users(self, organization):
		"""
		check whether this user may list all users of this organization
		:param str organization: name of the organization
		"""
		# global admins and admins of the respective organization may do this.
		if Flags.GlobalAdmin in self.get_flags():
			return
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == organization:
			return
		auth_fail("operation requires global or organization-internal admin flag")

	def account_info_visible_keys(self, userB):
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
		:rtype: list(str)
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

	def check_may_reset_password_of_user(self, userB):
		"""
		check whether this user may reset the password for userB.
		:param UserInfo userB: user whose password is to be resetted.
		"""
		if userB.get_username() == self.get_username():
			return
		if Flags.GlobalAdmin in self.get_flags():
			return
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			return
		auth_fail("operation requires global or organization-internal admin flag")

	def check_may_delete_user(self, userB):
		"""
		check whether this user may delete userB
		:param UserInfo userB: user to be deleted
		"""
		if userB.get_username() == self.get_username():
			if Flags.GlobalAdmin in self.get_flags():
				auth_fail("admins may not delete themselves")
			return
		if Flags.GlobalAdmin in self.get_flags():
			return
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			if Flags.GlobalAdmin in userB.get_flags():
				auth_fail("organization-internal admins may not delete global admins")
			return
		auth_fail("operation requires global or organization-internal admin flag")

	def check_may_broadcast_messages(self, organization=None):
		"""
		check whether this user may broadcast messages
		:param None or str organization: if None, check whether broadcast to all is allowed. otherwise, check for this organization.
		"""
		flags = self.get_flags()
		if Flags.GlobalAdmin in flags or Flags.GlobalHostManager in flags:
			return
		if organization is None:
			auth_fail("operation requires global admin or hostmanager flag")

		if (Flags.OrgaAdmin in flags or Flags.OrgaHostManager in flags) and self.get_organization() == organization:
			return
		auth_fail("operation requires global or organization-internal admin or hostmanager flag")

	def check_may_send_message_to_user(self, userB):
		"""
		check whether this user may send a message to userB
		:param UserInfo userB: receiver of the message
		"""
		if userB.get_username() == self.get_username():
			return
		if Flags.GlobalAdmin in self.get_flags():
			return
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			return
		auth_fail("operation requires global or organization-internal admin flag")





	# organizations

	def check_may_create_organizations(self):
		"""
		check whether this user may create an organization
		"""
		if Flags.GlobalHostManager in self.get_flags():
			return
		if Flags.GlobalAdmin in self.get_flags():
			return
		auth_fail("operation requires global admin or hostmanager flag")

	def check_may_modify_organization(self, organization):
		"""
		check whether this user may modify this organization
		:param str organization: organization to be modified
		"""
		if Flags.GlobalAdmin in self.get_flags() or Flags.GlobalHostManager in self.get_flags():
			return
		if (Flags.OrgaAdmin in self.get_flags() or Flags.OrgaHostManager in self.get_flags()) and self.get_organization() == organization:
			return
		auth_fail("operation requires global or organization-internal admin or hostmanager flag")

	def check_may_delete_organization(self, organization):
		"""
		check whether this user may delete this organization
		:param str organization: organization to be deleted
		"""
		if organization == self.get_organization():
			auth_fail("you may not delete your own organization")
		if Flags.GlobalAdmin in self.get_flags():
			return
		if Flags.GlobalHostManager in self.get_flags():
			return
		auth_fail("operation requires global admin or hostmanager flag")



	# sites

	def _check_is_hostmanager_for_organization(self, organization):
		"""
		check whether this user is hostmanager for the given organization
		:param str organization: target organization's name
		"""
		if Flags.GlobalHostManager in self.get_flags():
			return
		if Flags.OrgaHostManager in self.get_flags() and organization == self.get_organization():
			return
		auth_fail("operation requires global or organization-internal hostmanager flag")

	def check_may_create_sites(self, organization):
		"""
		check whether this user may create sites for this organization
		:param str organization: target site's organization
		"""
		self._check_is_hostmanager_for_organization(organization)

	def check_may_modify_site(self, site_info):
		"""
		check whether this user may modify this site
		:param SiteInfo site_info: target site
		"""
		self._check_is_hostmanager_for_organization(site_info.get_organization())

	def check_may_delete_site(self, site_info):
		"""
		check whether this user may delete this site
		:param SiteInfo site_info: target site
		"""
		self._check_is_hostmanager_for_organization(site_info.get_organization())




	# hosts

	def check_may_create_hosts(self, site_info):
		"""
		check whether this user may create hosts for this site
		:param SiteInfo site_info: target hosts's site
		"""
		self._check_is_hostmanager_for_organization(site_info.get_organization())

	def check_may_modify_host(self, host_info):
		"""
		check whether this user may modify this host
		:param HostInfo host_info: target host
		"""
		self._check_is_hostmanager_for_organization(host_info.get_organization())

	def check_may_delete_host(self, host_info):
		"""
		check whether this user may delete this host
		:param HostInfo host_info: target host
		"""
		self._check_is_hostmanager_for_organization(host_info.get_organization())

	def check_may_list_host_users(self, host_info):
		"""
		check whether this user may list users of this host
		:param HostInfo host_info: target host
		"""
		self._check_is_hostmanager_for_organization(host_info.get_organization())






	# topologies

	def _check_has_topology_role(self, topology_info, role):
		"""
		check whether the user has a given role on the topology.
		return True if the user has a higher role.
		this also checks for user permission flags like GlobalToplManager.

		:param TopologyInfo topology_info: target topology info
		:param str role: target role
		"""
		# first, try to resolve this without topology information
		perm_global, perm_orga = Flags.getMaxTopologyFlags(self.get_flags())
		if Role.leq(role, perm_global):
			return

		if topology_info.user_has_role(self.get_username(), role):
			return
		if Role.leq(role, perm_orga):  # user has role in organization
			if topology_info.organization_has_role(self.get_organization(), role):  # organization has role on topology
				return
		auth_fail("this operation requires %s permission on this toppology." % role)

	def check_may_create_topologies(self):
		"""
		check whether this user may create topologies.
		"""
		auth_check(Flags.NoTopologyCreate not in self.get_flags(), "you are not allowed to create topologies")

	def check_may_view_topology(self, topology_info):
		"""
		check whether this user may view this topology.
		:param TopologyInfo topology_info: target topology
		"""
		self._check_has_topology_role(topology_info, Role.user)

	def check_may_remove_topology(self, topology_info):
		"""
		check whether this user may remove this topology.
		:param TopologyInfo topology_info: target topology
		"""
		self._check_has_topology_role(topology_info, Role.owner)

	def check_may_modify_topology(self, topology_info):
		"""
		check whether this user may modify this topology.
		:param TopologyInfo topology_info: target topology
		"""
		self._check_has_topology_role(topology_info, Role.owner)

	def check_may_run_topology_actions(self, topology_info):
		"""
		check whether this user may run actions on this topology.
		:param TopologyInfo topology_info: target topology
		"""
		self._check_has_topology_role(topology_info, Role.manager)

	def _may_list_all_topologies(self):
		"""
		check whether this user may see info of all topologies.
		:return: if this is allowed
		:rtype: bool
		"""
		for flag in (Flags.GlobalToplUser, Flags.GlobalToplManager, Flags.GlobalToplOwner):
			if flag in self.get_flags():
				return True
		return False

	def check_may_list_all_topologies(self):
		"""
		check whether this user may see info of all topologies.
		"""
		auth_check(self._may_list_all_topologies(), "this operation requires the global topology user permission")

	def check_may_list_organization_topologies(self, organization):
		"""
		check whether this user may see info of all topologies of this organization.
		:param str organization: name of target organization
		"""
		if self._may_list_all_topologies():
			return
		auth_check(self.get_organization() == organization, "no permissions to list all topologies of this organization")
		for flag in (Flags.OrgaToplUser, Flags.OrgaToplManager, Flags.OrgaToplOwner):
			if flag in self.get_flags():
				return
		auth_fail("no permissions to list all topologies of an organization")

	def check_may_grant_permission_for_topologies(self, topology_info, role, username):
		"""
		check whether this user may grant another user this permission on this topology.
		:param str role: target role as in auth.permissions.Role
		:param TopologyInfo topology_info: target topology
		:param str username: target user
		:return: whether this user may grant this permission on this topology.
		:rtype: bool
		"""
		auth_check(username != self.get_username(), "you may not change your own permissions")
		auth_check(self._has_topology_role(topology_info, role), "you can only grant permissions that you have for yourself")

	def check_may_view_topology_usage(self, topology_info):
		if Flags.GlobalHostManager in self.get_flags():
			return
		if Flags.GlobalAdmin in self.get_flags():
			return
		if topology_info.organization_has_role(self.get_organization(), Role.user):
			if Flags.OrgaAdmin in self.get_flags():
				return
			if Flags.OrgaHostManager in self.get_flags():
				return
		self._check_has_topology_role(topology_info, Role.user)





	# debugging

	def check_may_view_debugging_info(self):
		auth_check(Flags.Debug in self.get_flags(), "you don't have debugging permissions")

	def check_may_execute_tasks(self):
		#fixme: this is what was checked in api before. I think this should check for debug permissions...
		auth_check(Flags.GlobalAdmin in self.get_flags(), "you don't have permissions to execute tasks")







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
