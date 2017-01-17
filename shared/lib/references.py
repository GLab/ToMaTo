__author__ = 't-gerhard'

class Reference:
	TOPOLOGY = 'topology'
	@staticmethod
	def topology(id):
		return (Reference.TOPOLOGY, id)

	HOST = 'host'
	@staticmethod
	def host(name):
		return (Reference.HOST, name)

	SITE = 'site'
	@staticmethod
	def site(name):
		return (Reference.SITE, name)

	ORGANIZATION = 'organization'
	@staticmethod
	def organization(name):
		return (Reference.ORGANIZATION, name)

	ACCOUNT = 'account'
	@staticmethod
	def account(name):
		return (Reference.ACCOUNT, name)

	TEMPLATE = 'template'
	@staticmethod
	def template(id):
		return (Reference.TEMPLATE, id)

	PROFILE = 'profile'
	@staticmethod
	def profile(id):
		return (Reference.PROFILE, id)

	ERRORGROUP = "errorgroup"
	@staticmethod
	def errorgroup(group_id):
		return (Reference.ERRORGROUP, group_id)


	ONSCREEN = {
		TOPOLOGY: 'Topology',
		HOST: 'Host',
		SITE: 'Site',
		ORGANIZATION: 'Organization',
		ACCOUNT: 'User Account',
		TEMPLATE: 'Template',
		PROFILE: 'Device Profile',
		ERRORGROUP: "Error Group"
	}

	KEYS = {
		TOPOLOGY: ('id'),
		HOST: ('name'),
		SITE: ('name'),
		ORGANIZATION: ('name'),
		ACCOUNT: ('name'),
		TEMPLATE: ('id'),
		PROFILE: ('id'),
		ERRORGROUP: ('group_id')
	}

