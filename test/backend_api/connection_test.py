from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class ConnectionTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_other_accounts()
		cls.remove_all_templates()
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_hosts()



		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)
			host_name = cls.get_host_name(host)
			cls.proxy_holder.backend_core.host_action(host_name, "forced_update")

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
		
		cls.testelement1_attrs = {
			"profile": "normal",
			"name": "Ubuntu 12.04 (x86) #1",
			"template":  "ubuntu-12.04_x86"
			}

		cls.testelement1 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id, type=cls.test_temps[0]['tech'], attrs=cls.testelement1_attrs)
		cls.testelement1_id = cls.testelement1['id']

		cls.testelement1_interface = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech']+"_interface",
																		parent=cls.testelement1_id)
		cls.testelement1_interface_id = cls.testelement1_interface["id"]

		cls.testelement2_attrs = {
			"profile": "normal",
			"name": "Ubuntu 12.04 (x86) #2",
			"template": "ubuntu-12.04_x86"
			}

		cls.testelement2 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech'],
																		attrs=cls.testelement2_attrs)
		cls.testelement2_id = cls.testelement2['id']

		cls.testelement2_interface = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech']+"_interface",
																		parent=cls.testelement2_id)
		cls.testelement2_interface_id = cls.testelement2_interface["id"]
		cls.proxy_holder.backend_core.topology_action(cls.testtopology_id,"start")


	def setUp(self):

		self.testconnection = self.proxy_holder.backend_core.connection_create(self.testelement1_interface_id, self.testelement2_interface_id)
		self.testconnection_id = self.testconnection["id"]

	def tearDown(self):
		self.remove_all_connections()
		self.remove_all_elements()


	@classmethod
	def tearDownClass(cls):

		cls.proxy_holder.backend_core.topology_action(cls.testtopology_id,"stop")
		cls.remove_all_other_accounts()
		cls.remove_all_templates()
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_hosts()

	def test_element_list(self):
		print "hello world"