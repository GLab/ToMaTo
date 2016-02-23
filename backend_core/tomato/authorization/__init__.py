from ..lib.userflags import Flags
from info import UserInfo

class PermissionChecker(UserInfo):
	def __init__(self, username):
		super(PermissionChecker, self).__init__(username)

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
			res.update('email', 'flags', 'organization', 'quota', 'client_data', 'last_login', 'password_hash')
		if Flags.GlobalAdmin in self.get_flags() or \
				Flags.OrgaAdmin in self.get_flags() and self.get_organization() == userB.get_organization():
			res.update('email', 'flags', 'organization', 'quota', 'notification_count', 'client_data', 'last_login', 'password_hash')
		return res

	def modify_allowed_keys(self, userB):
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
				result.update("realname", "email", "organization")
			if Flags.OrgaAdmin in self.get_flags() and self.info['organization'] == userB.get_organization():
				result.update("realname", "email")
		return result

	def modify_allowed_flags(self, userB):
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

	def may_reset_password(self, userB):
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

	def may_delete(self, userB):
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

	def may_send_message(self, userB):
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

_user_infos = {}

def get_user_info(username):
	"""
	get user info for this username
	This may be cached, or fresh.
	:param str username: username of user
	:return: UserInfo object for corresponding user
	:rtype: UserInfo
	"""
	if username not in _user_infos:
		user_info = UserInfo(username=username)
		_user_infos[username] = user_info
	return _user_infos[username]