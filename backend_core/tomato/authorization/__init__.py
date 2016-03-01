from ..lib.userflags import Flags
from info import UserInfo, TopologyInfo
from ..auth.permissions import Role

class PermissionChecker(UserInfo):
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
		return Flags.GlobalAdmin in self.get_flags()

	def may_modify_organization(self, organization):
		"""
		check whether this user may modify this organization
		:param str organization: organization to be modified
		:return: whether this user may modify this organization
		:rtype: bool
		"""
		if Flags.GlobalAdmin in self.get_flags():
			return True
		if Flags.OrgaAdmin in self.get_flags() and self.get_organization() == organization:
			return True
		return False

	def may_delete_organization(self, organization):
		"""
		check whether this user may delete this organization
		:param str organization: organization to be deleted
		:return: whether this user may delete this organization
		:rtype: bool
		"""
		return Flags.GlobalAdmin in self.get_flags()





	# topologies

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
		return topology_info.hasRole(self.get_username(), Role.user)
		#fixme: global or orga topology roles are not respected.

	def may_remove_topology(self, topology_info):
		"""
		check whether this user may remove this topology.
		:param TopologyInfo topology_info: target topology
		:return: whether this user may remove this topology.
		:rtype: bool
		"""
		return topology_info.hasRole(self.get_username(), Role.owner)
		#fixme: global or orga topology roles are not respected.

	def may_modify_topology(self, topology_info):
		"""
		check whether this user may modify this topology.
		:param TopologyInfo topology_info: target topology
		:return: whether this user may modify this topology.
		:rtype: bool
		"""
		return topology_info.hasRole(self.get_username(), Role.owner)
		#fixme: global or orga topology roles are not respected.

	def may_run_topology_actions(self, topology_info):
		"""
		check whether this user may run actions on this topology.
		:param TopologyInfo topology_info: target topology
		:return: whether this user may run actions on this topology.
		:rtype: bool
		"""
		return topology_info.hasRole(self.get_username(), Role.manager)
		#fixme: global or orga topology roles are not respected.

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
		return topology_info.hasRole(self.get_username(), role) and not (username == self.get_username())
		# fixme: todiscuss: may global/orga topl managers/etc grant permissions?











_permission_checkers = {}

def get_permission_checker(username):
	"""
	get PermissionChecker for this username
	:param str username: username of user
	:return: PermissionChecker object for corresponding user
	:rtype: PermissionChecker
	"""
	if username not in _permission_checkers:
		permission_checker = PermissionChecker(username=username)
		_permission_checkers[username] = permission_checker
	return _permission_checkers[username]

def get_user_info(username):
	"""
	return UserInfo object for this username
	:param str username: username of user
	:return: PermissionChecker object for corresponding user
	:rtype: PermissionChecker
	"""
	return get_permission_checker(username)

def get_topology_info(topology_id):
	"""
	return TopologyInfo object for the respective topology
	:param topology_id: id of topology
	:return: TopologyInfo object
	:rtype: TopologyInfo
	"""
	return TopologyInfo(topology_id)
