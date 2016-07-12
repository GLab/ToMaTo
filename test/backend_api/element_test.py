from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class ElementTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()

		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)

		cls.add_templates_if_missing()

		for temp in cls.proxy_holder.backend_core.template_list():
			if temp['name'] == cls.test_temps[0]['name']:
				cls.test_temp1_id = temp['id']

		# Create test profile for openvz
		cls.testprofile_tech = "openvz"
		cls.testprofile_name = "normal"
		cls.testprofile_args = {'diskspace': 10240, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal',
								 'preference': 10, 'description': 'Test profile'}

		cls.proxy_holder.backend_core.profile_create(cls.testprofile_tech, cls.testprofile_name,
													 cls.testprofile_args)

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
			"profile": self.testprofile_name,
			"name": "Ubuntu 12.04 (x86) #1",
			"template":  self.test_temps[0]['name']
			}

		self.testelement = self.proxy_holder.backend_core.element_create(top=self.testtopology_id, type=self.test_temps[0]['tech'], attrs=self.testelement_attrs)
		self.testelement_id = self.testelement['id']

		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "start")


	def tearDown(self):
		self.remove_all_elements()


	@classmethod
	def tearDownClass(cls):
		cls.proxy_holder.backend_core.topology_action(cls.testtopology_id,"stop")

		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()


	#Just check if element info will be returned without modification
	def test_element_info(self):
		element_info_api = self.proxy_holder.backend_api.element_info(self.testelement_id)
		element_info_core = self.proxy_holder.backend_core.element_info(self.testelement_id)
		self.assertDictEqual(element_info_api, element_info_core)

	#Check if permissions are checked for element info
	def test_element_info_without_permission(self):
		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.element_info, self.testelement_id)

	def test_element_info_non_existing(self):

		testelement_id = self.testelement_id[12:24] + self.testelement_id[0:12]

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_info, testelement_id)