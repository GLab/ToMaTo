from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class CapabilitiesTestCase(ProxyHoldingTestCase):

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
			host_name = cls.get_host_name(host)
			cls.proxy_holder.backend_core.host_action(host_name, "forced_update")

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

	def test_capabilities_element_correct_type(self):
		self.assertDictEqual(self.proxy_holder.backend_api.capabilities_element("openvz"), self.proxy_holder.backend_core.capabilities_element("openvz"))

	@unittest.skip("Cached Information - Check how to manually update this for testing")
	def test_capabilities_element_correct_type_but_wrong_host(self):
		template_list_core = self.proxy_holder.backend_core.template_list()
		self.proxy_holder.backend_core.template_remove(template_list_core[template_list_core.__len__()-1]["id"])
		print self.proxy_holder.backend_api.capabilities_element(template_list_core[template_list_core.__len__()-1]["tech"])
		print self.proxy_holder.backend_core.capabilities_element(template_list_core[template_list_core.__len__()-1]["tech"])

	def test_capabilities_element_non_exisent_type(self):
		self.assertRaisesError(UserError,UserError.UNSUPPORTED_TYPE,self.proxy_holder.backend_api.capabilities_element,"NoTech")

	def test_capabilites_connection_correct(self):
		self.assertDictEqual(self.proxy_holder.backend_api.capabilities_connection("bridge"), self.proxy_holder.backend_core.capabilities_connection("bridge"))

	def test_capabilities_connection_wrong_type(self):
		self.assertRaisesError(UserError, UserError.INVALID_CONFIGURATION, self.proxy_holder.backend_api.capabilities_connection,"NoTech")

	def test_capabilities(self):
		self.assertDictEqual(self.proxy_holder.backend_api.capabilities(), self.proxy_holder.backend_core.capabilities())
