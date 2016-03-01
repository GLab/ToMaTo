from userflags import Flags

class Role:
	owner = "owner" # full topology control, permission changes, topology removal
	manager = "manager" # full topology control, no topology delete, no permission changes
	user = "user" # no destroy/prepare, no topology changes, no permission changes
	null = "null" # no access at all

	RANKING=[null, user, manager, owner]

	@staticmethod
	def max(role_1, role_2):
		return Role.RANKING[max(Role.RANKING.index(role_1), Role.RANKING.index(role_2))]

	@staticmethod
	def min(role_1, role_2):
		return Role.RANKING[min(Role.RANKING.index(role_1), Role.RANKING.index(role_2))]

	@staticmethod
	def leq(role_1, role_2):
		"""
		check whether role_1 <= role_2
		:param str role_1:
		:param str role_2:
		:return: role_1 <= role_2
		:rtype: bool
		"""
		return Role.RANKING.index(role_1) <= Role.RANKING.index(role_2)

	@staticmethod
	def get_flag_topology_permissions(flags):
		"""
		select the maximum permissions for topologies for global and organization-internal
		:param list(str) flags: user flags
		:return: maximum global permission, maximum orga-internal permission
		:rtype: tuple(bool)
		"""
		max_global = "null"
		max_orga = "null"
		for flag in [Flags.GlobalToplUser, Flags.GlobalToplManager, Flags.GlobalToplOwner]:
			if flag in flags:
				max_global = flag
		for flag in [Flags.OrgaToplUser, Flags.OrgaToplManager, Flags.OrgaToplOwner]:
			if flag in flags:
				max_orga = flag
		return Role.from_user_flag(max_global), Role.from_user_flag(max_orga)

	@staticmethod
	def from_user_flag(flag):
		"""
		convert a Topology permission flag (e.g., OrgaToplUser) to a topology Role
		:param str flag: flag as in userflags.Flags
		:return: corresponding Role
		:rtype: str
		"""
		if flag in (Flags.GlobalToplOwner, Flags.OrgaToplOwner):
			return "owner"
		if flag in (Flags.GlobalToplManager, Flags.OrgaToplManager):
			return "manager"
		if flag in (Flags.GlobalToplUser, Flags.OrgaToplUser):
			return "user"
		return "null"



def role_descriptions():
	return {
		Role.owner:	{	'title': "Owner",
						'description':"full topology control, permission changes, topology removal"},

		Role.manager:{	'title': "Manager",
						'description':"full topology control, no topology delete, no permission changes"},

		Role.user:	{	'title': "User",
						'description':"no destroy/prepare, no topology changes, no permission changes"},

		Role.null:	{	'title': "[no permission]",
						'description':"no access at all"}
	}