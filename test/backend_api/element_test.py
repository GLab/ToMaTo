from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class ElementTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_hosts()
		cls.remove_all_other_accounts()
		cls.remove_all_templates()
		cls.remove_all_elements()
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

		cls.testtopology = cls.proxy_holder.backend_core.topology_create(cls.default_user_name)
		cls.testtopology_id = cls.testtopology['id']




	def setUp(self):
		self.testelement_attrs = {
			"profile": "normal",
			"name": "Ubuntu 12.04 (x86) #1",
			"template":  "ubuntu-12.04_x86"
			}

		self.testelement = self.proxy_holder.backend_core.element_create(top=self.testtopology_id, type=self.test_temps[0]['tech'], attrs=self.testelement_attrs)
		self.testelement_id = self.testelement['id']


	def tearDown(self):
		self.remove_all_elements()


	@classmethod
	def tearDownClass(cls):
		cls.remove_all_hosts()
		cls.remove_all_other_accounts()
		cls.remove_all_templates()
		cls.remove_all_elements()
		cls.remove_all_topologies()

	def test_element_list(self):
		print "hello world"