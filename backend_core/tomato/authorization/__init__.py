from ..lib.userflags import Flags
from info import UserInfo, TopologyInfo, SiteInfo, HostInfo, ElementInfo, ConnectionInfo,\
	get_topology_info, get_host_info, get_site_info, get_element_info, get_connection_info
from ..lib.topology_role import Role
from ..lib.cache import cached
from ..lib.error import UserError
from ..lib.service import get_tomato_inner_proxy
from ..lib.settings import Config

import time

def auth_check(condition, message, data=None):
	if not data:
		data = {}
	UserError.check(condition, code=UserError.DENIED, message=message, data=data)

def auth_fail(message, data=None):
	auth_check(False, message, data)


class PermissionChecker(UserInfo):
	__slots__ = ("success_password", "password_age")

	def __init__(self, username):
		super(PermissionChecker, self).__init__(username)
		self.success_password = None
		self.password_age = 0

	def invalidate_info(self):
		super(PermissionChecker, self).invalidate_info()
		self.success_password = None





	# authentication

	def login(self, password):

		# if password is cached, try to use the cached one if it isn't too old.
		if self.success_password:
			if time.time() - self.password_age > self.cache_duration:
				self.success_password = None
			else:
				if password == self.success_password:
					return True  # if false, this may be due to a recent password changed that hasn't been seen by the cache.
											# in this case, try to get a fresh password.

		api = get_tomato_inner_proxy(Config.TOMATO_MODULE_BACKEND_USERS)
		result = api.user_check_password(self.get_username(), password)
		if result:
			self.password_age = time.time()
			self.success_password = password
		return result







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

	def check_may_create_user(self, user_info):
		"""
		check whether this user may create a user for the given organization
		:param UserInfo user_info: target user
		"""
		if Flags.GlobalAdmin in self.get_flags():
			return
		if Flags.OrgaAdmin in self.get_flags() and user_info.get_organization() == self.get_organization():
			return
		auth_fail("You need admin permissions to create other users.")

	@staticmethod
	def account_register_self_allowed_keys():
		return {"name", "realname", "email", "password", "organization"}

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

	@staticmethod
	def reduce_keys_to_allowed(attrs, allowed_keys, allowed_flags, ignore_key_on_unauthorized=False, ignore_flag_on_unauthorized=False):
		"""
		check if all editing keys are correct.
		if not, either throw an error, or ignore the key, depending on the settings in params

		:param dict attrs: origninal attributes to check
		:param list(str) allowed_keys: attrs keys that are allowed to be modified
		:param list(str) allowed_flags: flags that are allowed to be set
		:param bool ignore_key_on_unauthorized: if true, ignore unauthorized keys. if false, throw an error if an unauthorized key was found.
		:param bool ignore_flag_on_unauthorized: if true, ignore unauthorized flags. if false, throw an error if an unauthorized flag was found.
		:return: an updated version of attrs where only allowed keys are present
		:rtype: dict
		"""
		res = {}
		for k, v in attrs.iteritems():
			if k in allowed_keys:
				if k == "flags":
					final_flags = {}
					for flag, toset in v.iteritems():
						if flag in allowed_flags:
							final_flags[flag] = toset
						else:
							if not ignore_flag_on_unauthorized:
								auth_fail("You are not allowed to set this flag", data={"flag": flag})
					res[k] = final_flags
				else:
					res[k] = v
			else:
				if not ignore_key_on_unauthorized:
					auth_fail("You are not allowed to set this key.", data={"key": k})
		return res


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

	def check_may_run_topology_action(self, topology_info, action):
		"""
		check whether this user may run this action on this topology.
		:param TopologyInfo topology_info: target topology
		:param str action: target action
		"""
		# step 1: make sure the user doesn't run any unrecognized action
		# fixme: is this complete? add more available actions.
		UserError.check(action in ("start", "stop", "prepare", "destroy"),
										code=UserError.UNSUPPORTED_ACTION, message="Unsupported action", data={"action": action})

		# step 2: check permission for each individual action
		if action in ("start", "stop", "prepare", "destroy"):
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





	# resources

	def check_may_create_user_resources(self):
		"""
		check whether this user may create user resources (e.g. Templates, Profiles)
		"""
		auth_check(Flags.GlobalAdmin in self.get_flags(), "you don't have permissions to create user resources.")

	def check_may_modify_user_resources(self):
		"""
		check whether this user may modify user resources (e.g. Templates, Profiles)
		"""
		auth_check(Flags.GlobalAdmin in self.get_flags(), "you don't have permissions to modify user resources.")

	def check_may_remove_user_resources(self):
		"""
		check whether this user may delete user resources (e.g. Templates, Profiles)
		"""
		auth_check(Flags.GlobalAdmin in self.get_flags(), "you don't have permissions to remove user resources.")

	def check_may_create_technical_resources(self):
		"""
		check whether this user may create technical resources (e.g. Templates, Profiles)
		"""
		auth_check(Flags.GlobalHostManager in self.get_flags(), "you don't have permissions to create technical resources.")

	def check_may_modify_technical_resources(self):
		"""
		check whether this user may modify technical resources (e.g. Templates, Profiles)
		"""
		auth_check(Flags.GlobalHostManager in self.get_flags(), "you don't have permissions to modify technical resources.")

	def check_may_remove_technical_resources(self):
		"""
		check whether this user may delete technical resources (e.g. Templates, Profiles)
		"""
		auth_check(Flags.GlobalHostManager in self.get_flags(), "you don't have permissions to remove technical resources.")





	# elements

	def check_may_create_element(self, topology_info):
		"""
		check whether this user may create elements on this topology
		:param TopologyInfo topology_info: target topology
		"""
		self._check_has_topology_role(topology_info, Role.manager)

	def check_may_modify_element(self, element_info):
		"""
		check whether this user may modify this element
		:param ElementInfo element_info: target element
		"""
		self._check_has_topology_role(element_info.get_topology_info(), Role.manager)

	def check_may_remove_element(self, element_info):
		"""
		check whether this user may delete this element
		:param ElementInfo element_info: target element
		"""
		self._check_has_topology_role(element_info.get_topology_info(), Role.manager)

	def check_may_view_element(self, element_info):
		"""
		check whether this user may view this element
		:param ElementInfo element_info: target element
		"""
		self._check_has_topology_role(element_info.get_topology_info(), Role.user)

	def check_may_run_element_action(self, element_info, action):
		"""
		check whether this user may run this action on the given element
		:param ElementInfo element_info: target element
		:param str action: action to run
		"""
		# step 1: make sure the user doesn't run any action that is not recognized by this.
		# fixme: this is not complete. add more available actions.
		UserError.check(action in ("start", "stop", "prepare", "destroy"),
										code=UserError.UNSUPPORTED_ACTION, message="Unsupported action", data={"action": action})

		# step 2: for each action, check permissions.
		if action in ("start", "stop", "prepare", "destroy"):
			self._check_has_topology_role(element_info.get_topology_info(), Role.manager)





	# connections

	def check_may_create_connection(self, element_info_1, element_info_2):
		"""
		check whether this user may run create a connection between the given elements
		:param ElementInfo element_info_1: first target element
		:param ElementInfo element_info_2: second target element
		"""
		el1_top_info = element_info_1.get_topology_info()
		auth_check(el1_top_info.get_id() == element_info_2.get_topology_info().get_id(), "Elements must be from the same topology.")
		self._check_has_topology_role(el1_top_info, Role.manager)  # element 2 has the same topology, so only one check needed

	def check_may_modify_connection(self, connection_info):
		"""
		check whether this user may modify this connection
		:param ConnectionInfo connection_info: target connection
		"""
		self._check_has_topology_role(connection_info.get_topology_info(), Role.manager)

	def check_may_remove_connection(self, connection_info):
		"""
		check whether this user may remove this connection
		:param ConnectionInfo connection_info: target connection
		"""
		self._check_has_topology_role(connection_info.get_topology_info(), Role.manager)

	def check_may_view_connection(self, connection_info):
		"""
		check whether this user may view this connection
		:param ConnectionInfo connection_info: target connection
		"""
		self._check_has_topology_role(connection_info.get_topology_info(), Role.user)

	def check_may_run_connection_action(self, connection_info, action):
		"""
		check whether this user may run this action on the given connection
		:param ConnectionInfo connection_info: target connection
		:param str action: action to run
		"""
		# step 1: make sure the user doesn't run any action that is not recognized by this.
		# fixme: is this complete? add more available actions.
		UserError.check(action in ("start", "stop", "prepare", "destroy"),
										code=UserError.UNSUPPORTED_ACTION, message="Unsupported action", data={"action": action})

		# step 2: for each action, check permissions.
		if action in ("start", "stop", "prepare", "destroy"):
			self._check_has_topology_role(connection_info.get_topology_info(), Role.manager)





	# debugging

	def check_may_view_debugging_info(self):
		auth_check(Flags.Debug in self.get_flags(), "you don't have debugging permissions")

	def check_may_execute_tasks(self):
		#fixme: this is what was checked in api before. I think this should check for debug permissions...
		auth_check(Flags.GlobalAdmin in self.get_flags(), "you don't have permissions to execute tasks")








class PseudoUser(UserInfo):
	"""
	UserInfo-like object for non-existing users.
	"""
	__slots__ = ("organization",)

	def __init__(self, username, organization):
		super(PseudoUser, self).__init__(username)
		self.organization = organization

	def _fetch_data(self):
		return {
			'organization': self.organization,
			'name': self.name
		}





def login(username, password):
	user_info = get_permission_checker(username)
	if user_info.login(password):
		return user_info
	else:
		return None


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

def get_pseudo_user_info(username, organization):
	"""
	return UserInfo object for a non-existing user
	:param str username: username of user
	:return: PermissionChecker object for corresponding user
	:rtype: PermissionChecker
	"""
	return PseudoUser(username, organization)

