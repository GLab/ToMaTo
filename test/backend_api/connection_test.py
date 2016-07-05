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
		cls.add_profiles()

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
			"profile": cls.default_profile_name,
			"name": "Ubuntu 12.04 (x86) #1",
			"template":  cls.test_temps[0]['name']
			}

		cls.testelement1 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech'],
																		attrs=cls.testelement1_attrs)
		cls.testelement1_id = cls.testelement1['id']

		cls.testelement2_attrs = {
			"profile": cls.default_profile_name,
			"name": "Ubuntu 12.04 (x86) #2",
			"template":  cls.test_temps[0]['name']
			}

		cls.testelement2 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech'],
																		attrs=cls.testelement2_attrs)
		cls.testelement2_id = cls.testelement2['id']

		cls.testelement2_interface = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech']+"_interface",
																		parent=cls.testelement2_id)
		cls.testelement2_interface_id = cls.testelement2_interface["id"]

		cls.testelement3_attrs = {
			"profile": cls.default_profile_name,
			"name": "Ubuntu 12.04 (x86) #3",
			"template":  cls.test_temps[0]['name']
			}

		cls.testelement3 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech'],
																		attrs=cls.testelement3_attrs)
		cls.testelement3_id = cls.testelement3['id']

		cls.testelement3_interface = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																		type=cls.test_temps[0]['tech']+"_interface",
																		parent=cls.testelement3_id)
		cls.testelement3_interface_id = cls.testelement3_interface["id"]
		
		cls.testelement1_interface = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																				  type=cls.test_temps[0][
																						   'tech'] + "_interface",
																				  parent=cls.testelement1_id)
		cls.testelement1_interface_id = cls.testelement1_interface["id"]

		cls.testelement1_interface_2 = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																				  type=cls.test_temps[0][
																						   'tech'] + "_interface",
																				  parent=cls.testelement1_id)
		cls.testelement1_interface_2_id = cls.testelement1_interface_2["id"]

		cls.testelement2_interface = cls.proxy_holder.backend_core.element_create(top=cls.testtopology_id,
																				  type=cls.test_temps[0][
																						   'tech'] + "_interface",
																				  parent=cls.testelement2_id)
		cls.testelement2_interface_id = cls.testelement2_interface["id"]


	def setUp(self):
		

		self.testconnection = self.proxy_holder.backend_core.connection_create(self.testelement1_interface_id, self.testelement2_interface_id)
		self.testconnection_id = self.testconnection["id"]

		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "start")

	def tearDown(self):
		self.remove_all_connections()


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

	def test_connection_create_correct(self):
		"""
		tests whether backend_api.connection_create correctly creates a connection
		"""

		self.testconnection2 = self.proxy_holder.backend_api.connection_create(self.testelement1_interface_2_id,self.testelement3_interface_id)
		self.assertIsNotNone(self.testconnection2)

	def test_connection_create_correct_wo_permissions(self):
		"""
		tests whether backend_api.connection_create responds correctly when called without permissions
		"""

		self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.connection_create,self.testelement1_interface_id,self.testelement2_interface_id)

	def test_connection_create_missing_element(self):
		"""
		tests whether backend_api.connection_create responds correctly when called without 2 existing elements
		"""

		false_id = self.testelement1_interface_2_id[12:24] + self.testelement1_interface_2_id[0:12];
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.connection_create,false_id,self.testelement2_interface_id)

	def test_connection_modify_correct(self):
		"""
		tests whether backend_api.connection_modify correctly modifies the given connection
		"""

		attrs = {
			"bandwidth_to": 100,
			"bandwidth_from": 10

		}

		self.proxy_holder.backend_api.connection_modify(self.testconnection_id,attrs)
		bandwidth = self.proxy_holder.backend_core.connection_info(self.testconnection_id)["bandwidth_to"]
		self.assertEqual(bandwidth,100)

	def test_connection_modify_non_existing_attribute(self):
		"""
		tests whether backend_api.connection_modify responds correctly when given a non existing attribute
		"""

		attrs = {
			"bandwidth_all": 100,
			"bandwidth_from": 10

		}

		self.assertRaisesError(UserError,UserError.UNSUPPORTED_ATTRIBUTE,self.proxy_holder.backend_api.connection_modify,self.testconnection_id,attrs)

	def test_connection_modify_correct_wo_permissions(self):
		"""
		tests whether backend_api.connection_modify correctly responds when called without permissions
		"""

		attrs = {
			"bandwidth_to": 100,
			"bandwidth_from": 10

		}

		self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.connection_modify,self.testconnection_id,attrs)

	def test_connection_modify_non_existing_element(self):
		"""
		tests whether backend_api.connection_modify responds correctly when given a non existing elements
		"""

		attrs = {
			"bandwidth_all": 100,
			"bandwidth_from": 10

		}
		false_id = self.testelement1_interface_2_id[12:24] + self.testelement1_interface_2_id[0:12];
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.connection_modify,false_id,attrs)

	def test_connection_remove_correct(self):
		"""
		tests whether backend_api.connection_remove() correctly removes the given connection
		"""

		self.proxy_holder.backend_api.connection_remove(self.testconnection_id)
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_core.connection_info,self.testconnection_id)
