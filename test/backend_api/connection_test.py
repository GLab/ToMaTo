from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class ConnectionTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_other_accounts()
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_hosts()



		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)
			host_name = cls.get_host_name(host)
			cls.proxy_holder.backend_core.host_action(host_name, "forced_update")

		cls.add_templates_if_missing()


		# Create test profile for openvz
		cls.testprofile_tech = cls.test_temps[0]['tech']
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


		#Create empty  testtopology
		cls.testtopology = cls.proxy_holder.backend_core.topology_create(cls.default_user_name)
		cls.testtopology_id = cls.testtopology['id']

		#Add two elements to test topology
		cls.testelement1_attrs = {
			"profile": cls.testprofile_name,
			"name": "Ubuntu 12.04 (x86) #1",
			"template":  cls.test_temps[0]['name']
			}

		cls.testelement1 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech'],
																		attrs=cls.testelement1_attrs)
		cls.testelement1_id = cls.testelement1['id']

		cls.testelement2_attrs = {
			"profile": cls.testprofile_name,
			"name": "Ubuntu 12.04 (x86) #2",
			"template":  cls.test_temps[0]['name']
			}

		cls.testelement2 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech'],
																		attrs=cls.testelement2_attrs)
		cls.testelement2_id = cls.testelement2['id']

		
		#Start topology (to save some time later)
		#cls.proxy_holder.backend_core.topology_action(cls.testtopology_id, "start")


	def setUp(self):
		self.testelement1_interface = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																				  type=self.test_temps[0][
																						   'tech'] + "_interface",
																				  parent=self.testelement1_id)
		self.testelement1_interface_id = self.testelement1_interface["id"]

		self.testelement2_interface = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																				  type=self.test_temps[0][
																						   'tech'] + "_interface",
																				  parent=self.testelement2_id)
		self.testelement2_interface_id = self.testelement2_interface["id"]

		self.testconnection = self.proxy_holder.backend_core.connection_create(self.testelement1_interface_id, self.testelement2_interface_id)
		self.testconnection_id = self.testconnection["id"]

		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "start")

	def tearDown(self):
		self.remove_all_connections()
		self.remove_all_elements()


	@classmethod
	def tearDownClass(cls):
		cls.proxy_holder.backend_core.topology_action(cls.testtopology_id,"stop")
		cls.remove_all_other_accounts()
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_hosts()

	def test_element_list(self):
		print "hello world"