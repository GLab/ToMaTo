from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class TopologyTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_hosts()
		cls.remove_all_other_accounts()
		cls.remove_all_templates()
		cls.remove_all_topologies()

		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)

		cls.add_templates_if_missing()

		# Create user without permission to create profiles
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = cls.default_organization_name
		testuser_attrs = {"realname": "Test User",
						  "email": "test@example.com",
						  "flags": {}
						  }
		cls.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization,
													testuser_attrs)
		cls.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)


	def setUp(self):
		self.testtopology = self.proxy_holder.backend_core.topology_create(self.default_user_name)
		self.testtopology_id = self.testtopology['id']


	def tearDown(self):
		self.remove_all_topologies()


	@classmethod
	def tearDownClass(cls):
		cls.remove_all_hosts()
		cls.remove_all_other_accounts()
		cls.remove_all_templates()
		cls.remove_all_topologies()

	def test_topology_list(self):
		print "hello world"