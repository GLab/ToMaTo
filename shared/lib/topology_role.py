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