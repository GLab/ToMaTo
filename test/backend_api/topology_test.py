from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import time
import unittest


class TopologyTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()
		cls.remove_all_other_organizations()
		cls.remove_all_hosts()

		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)

		cls.add_templates_if_missing()
		cls.add_profiles()

		# Create user without permission to create profiles
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = cls.default_organization_name
		testuser_attrs = {"realname": "Test User",
						  "email": "test@example.com",
						  "flags": {
							  "over_quota": True,
							  "no_topology_create":True
						  }
						  }
		cls.testuser_info = cls.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization,
													testuser_attrs)
		cls.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)

		# Create user with all permissions



		cls.testadmin_username = "testadmin"
		cls.testadmin_password = "123"
		cls.testadmin_organization = "DummyCorp"
		cls.testadmin_attrs = {"realname": "Test User Admin",
						  "email": "admin@example.com",
						  "flags": {
							  "global_admin": True,
							  "orga_admin": True,
							  "global_topl_owner": True,
							  "global_host_manager": True,
							  "debug": True
						  }
						  }

		cls.proxy_holder.backend_api.organization_create(cls.testadmin_organization)

		cls.proxy_holder.backend_api.account_create(cls.testadmin_username, cls.testadmin_password, cls.testadmin_organization,
													cls.testadmin_attrs)
		cls.proxy_holder_admin = ProxyHolder(cls.testadmin_username, cls.testadmin_password)


	def setUp(self):
		self.testtopology = self.proxy_holder.backend_core.topology_create(self.default_user_name)
		self.testtopology_id = self.testtopology['id']


	def tearDown(self):
		self.remove_all_connections()
		self.remove_all_elements()
		self.remove_all_topologies()


	@classmethod
	def tearDownClass(cls):
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()
		cls.remove_all_other_organizations()
		cls.remove_all_hosts()

	def test_topology_create_correct(self):
		"""
		Tests whether topology_create correctly creates a topology
		"""

		testtopology2 = self.proxy_holder.backend_api.topology_create()
		self.assertIsNotNone(testtopology2["id"])

	def test_topology_create_without_permissions(self):
		"""
		Tests whether topology_create correctly reponds when called without permissions
		"""

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.topology_create)

	def test_topology_remove_correct(self):
		"""
		Tests whether topology_remove correctly removes the given topology
		"""

		testtopology2 = self.proxy_holder.backend_api.topology_create()
		self.proxy_holder.backend_api.topology_remove(testtopology2["id"])

		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.topology_info,testtopology2["id"])

	def test_topology_remove_correct(self):
		"""
		Tests whether topology_remove correctly removes the given topology
		"""

		testtopology2 = self.proxy_holder.backend_api.topology_create()
		self.proxy_holder.backend_api.topology_remove(testtopology2["id"])

		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.topology_info,testtopology2["id"])

	def test_topology_remove_without_permission(self):
		"""
		Tests whether topology_remove correctly responds when called without suficient permissions
		"""

		testtopology2 = self.proxy_holder.backend_api.topology_create()

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.topology_remove,testtopology2["id"])

	def test_topology_remove_non_existing_topology(self):
		"""
		Tests whether topology_remove correctly responds when called with an invalid topology id
		"""
		testtopology2 = self.proxy_holder.backend_api.topology_create()
		false_id = testtopology2["id"][12:24] + testtopology2["id"][0:12]
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.topology_info,false_id)

	def test_topology_modify_correct(self):
		"""
		Tests whether topology_modify correctly modifies the given topology
		"""
		testtopology2 = self.proxy_holder.backend_api.topology_create()
		testtopology2_id = testtopology2["id"]
		attrs = {
			"name": "NewName"
		}

		self.proxy_holder.backend_api.topology_modify(testtopology2_id,attrs)
		self.assertEqual(self.proxy_holder.backend_core.topology_info(testtopology2_id)["name"],"NewName")

	def test_topology_modify_without_permissions(self):
		"""
		Tests whether topology_modify correctly responds when called without sufficient permissions
		"""
		attrs = {
			"name": "NewName"
		}
		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.topology_modify ,self.testtopology_id,attrs)

	def test_topology_modify_non_existing_topology(self):
		"""
		Tests whether topology_modify correctly responds when called with an invalid topology id
		"""
		attrs = {
			"name": "NewName"
		}
		false_id = self.testtopology["id"][12:24] + self.testtopology["id"][0:12]
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.topology_modify ,false_id,attrs)

	def test_topology_modify_non_existing_attribute(self):
		"""
		Tests whether topology_modify correctly responds when called with an invalid attribute
		"""
		testtopology2 = self.proxy_holder.backend_api.topology_create()
		testtopology2_id = testtopology2["id"]
		attrs = {
			"invalid": "invalid"
		}
		self.assertRaisesError(UserError,UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.topology_modify ,testtopology2_id,attrs)

	def test_topology_action_correct(self):
		"""
		Tests whether topology_action correctly applies the given action to the given topology
		"""
		testtopology2 = self.proxy_holder.backend_api.topology_create()
		testtopology2_id = testtopology2["id"]

		self.proxy_holder.backend_api.topology_action(testtopology2_id,"start")

	def test_topology_action_without_permissions(self):
		"""
		Tests whether topology_action correctly responds when called without sufficient permissions
		"""

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.topology_action,self.testtopology_id,"start")

	def test_topology_action_non_existing_topology(self):
		"""
		Tests whether topology_action correctly responds when called with an invali topology id
		"""
		false_id = self.testtopology["id"][12:24] + self.testtopology["id"][0:12]
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.topology_action,false_id,"start")

	def test_topology_action_non_existing_action(self):
		"""
		Tests whether topology_action correctly responds with an invalid action
		"""
		testtopology2 = self.proxy_holder.backend_api.topology_create()
		testtopology2_id = testtopology2["id"]

		self.assertRaisesError(UserError,UserError.UNSUPPORTED_ACTION,self.proxy_holder.backend_api.topology_action ,testtopology2_id,"noAction")

	def test_topology_info_correct(self):
		"""
		Tests whether topology_info returns the correct topologyInfo Object
		"""

		testtopology2 = self.proxy_holder.backend_api.topology_create()
		testtopology2_id = testtopology2["id"]

		self.assertEqual(self.proxy_holder.backend_api.topology_info(testtopology2_id) , self.proxy_holder.backend_core.topology_info(testtopology2_id))

	def test_topology_info_correct_full(self):
		"""
		Tests whether topology_info returns the correct topologyInfo Object
		"""

		testtopology2 = self.proxy_holder.backend_api.topology_create()
		testtopology2_id = testtopology2["id"]

		self.assertEqual(self.proxy_holder.backend_api.topology_info(testtopology2_id,True) , self.proxy_holder.backend_core.topology_info(testtopology2_id,True))

	def test_topology_info_non_existing_topology(self):
		"""
		Tests whether topology_info responds correctly when called with an invalid topology id
		"""
		false_id = self.testtopology["id"][12:24] + self.testtopology["id"][0:12]
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.topology_info,false_id)

	def test_topology_list_correct(self):
		"""
		Tests whether topology_list returns the correct list of topologies as the backend_core
		"""

		self.assertEqual(self.proxy_holder.backend_api.topology_list() , self.proxy_holder.backend_core.topology_list())

	def test_topology_list_correct_full(self):
		"""
		Tests whether topology_list returns the correct list of topologies as the backend_core
		"""

		self.assertEqual(self.proxy_holder.backend_api.topology_list(full=True) , self.proxy_holder.backend_core.topology_list(full=True))

	def test_topology_list_correct_all(self):
		"""
		Tests whether topology_list returns the correct list of topologies as the backend_core
		"""

		self.assertEqual(self.proxy_holder_admin.backend_api.topology_list(full=True,showAll=True) , self.proxy_holder_admin.backend_core.topology_list(full=True))

	def test_topology_list_correct_existing_orga(self):
		"""
		Tests whether topology_list returns the correct list of topologies as the backend_core
		"""

		testtopology2 = self.proxy_holder_admin.backend_api.topology_create()
		topology_list_api = self.proxy_holder_admin.backend_api.topology_list(full=True, organization=self.testadmin_organization)
		topology_list_core = self.proxy_holder_admin.backend_core.topology_list(full=True, organization_filter=self.testadmin_organization)

		self.assertEqual(topology_list_api,topology_list_core)

	def test_topology_list_correct_non_existing_orga(self):
		"""
		Tests whether topology_list responds correctly when called with an invalid organization
		"""
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.topology_list,organization="NoCorp")

	def test_topology_set_permission_correct(self):
		"""
		Tests whether topology_set_permissions correctly sets the desired permissions on the given topology
		"""

		testtopology2 = self.proxy_holder_admin.backend_api.topology_create()

		self.proxy_holder_admin.backend_api.topology_set_permission(testtopology2["id"],self.testuser_info["name"],"user")

	def test_topology_set_permission_to_none(self):
		"""
		Tests whether topology_set_permissions correctly sets the desired permissions on the given topology
		"""

		testtopology2 = self.proxy_holder_admin.backend_api.topology_create()

		self.proxy_holder_admin.backend_api.topology_set_permission(testtopology2["id"],self.testuser_info["name"],None)

	def test_topology_set_permission_without_permission(self):
		"""
		Tests whether topology_set_permissions correctly responds when called without sufficient permissions
		"""

		testtopology2 = self.proxy_holder_admin.backend_api.topology_create()
		testusername = self.testuser_info['name']
		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder.backend_api.topology_set_permission ,testtopology2["id"],testusername,"user")

	def test_topology_set_permission_non_existing_topology(self):
		"""
		Tests whether topology_set_permissions correctly responds when called with an invalid topology id
		"""
		false_id = self.testtopology["id"][12:24] + self.testtopology["id"][0:12]
		testusername = self.testuser_info['name']
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.topology_set_permission ,false_id,testusername,"user")

	def test_topology_set_permission_non_existing_user(self):
		"""
		Tests whether topology_set_permissions correctly responds when called with an invalid username
		"""

		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder_admin.backend_api.topology_set_permission,self.testtopology_id,"NoUserName","user")

	def test_topology_set_permission_non_existent_permission(self):
		"""
		Tests whether topology_set_permissions correctly responds when called with an invalid permission as argument
		"""

		testtopology2 = self.proxy_holder_admin.backend_api.topology_create()
		self.assertRaisesError(UserError,UserError.INVALID_VALUE, self.proxy_holder_admin.backend_api.topology_set_permission, testtopology2["id"],self.testuser_info["name"],"DaBoss")


	def test_topology_usage(self):
		"""
		tests whether the api returns correctly usage informations for a topology
		"""
		# Add two elements to test topology
		self.testelement1_attrs = {
			"profile": self.default_profile_name,
			"name": "Ubuntu 12.04 (x86) #1",
			"template": self.test_temps[0]['name']
		}

		self.testelement1 = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																		type=self.test_temps[0]['type'],
																		attrs=self.testelement1_attrs)
		self.testelement1_id = self.testelement1['id']

		self.testelement1_interface = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																				  type=self.testelement1['type'] + "_interface",
																				  parent=self.testelement1_id)
		self.testelement1_interface_id = self.testelement1_interface["id"]

		self.testelement2_attrs = {
			"profile": self.default_profile_name,
			"name": "Ubuntu 12.04 (x86) #2",
			"template": self.test_temps[0]['name']
		}

		self.testelement2 = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																		type=self.test_temps[0]['type'],
																		attrs=self.testelement2_attrs)
		self.testelement2_id = self.testelement2['id']

		self.testelement2_interface = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																				  type=self.testelement1['type'] + "_interface",
																				  parent=self.testelement2_id)
		self.testelement2_interface_id = self.testelement2_interface["id"]



		self.testconnection = self.proxy_holder.backend_core.connection_create(self.testelement1_interface_id, self.testelement2_interface_id)
		self.testconnection_id = self.testconnection["id"]

		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "start")

		self.testconnection = self.proxy_holder.backend_core.connection_info(self.testconnection_id)
		self.testelement1 = self.proxy_holder.backend_core.element_info(self.testelement1_id)
		self.testelement2 = self.proxy_holder.backend_core.element_info(self.testelement2_id)


		hostconnection_id = "%d@%s"%(self.testconnection['debug']['host_connections'][0][1],self.testconnection['debug']['host_connections'][0][0])
		hostelement1_id = "%d@%s"%(self.testconnection['debug']['host_elements'][0][1],self.testconnection['debug']['host_elements'][0][0])
		hostelement2_id = "%d@%s"%(self.testconnection['debug']['host_elements'][0][1],self.testconnection['debug']['host_elements'][0][0])


		self.proxy_holder.backend_accounting.push_usage(elements={hostelement1_id: [(int(time.time()), 0.0, 0.0, 0.0, 0.0)],hostelement2_id: [(int(time.time()), 0.0, 0.0, 0.0, 0.0)]}, connections={
			hostconnection_id: [(int(time.time()), 0.0, 0.0, 0.0, 0.0)]})
		connection_info_api = self.proxy_holder.backend_api.topology_usage(self.testtopology_id)
		connection_info_core = self.proxy_holder.backend_accounting.get_record("topology", self.testtopology_id)

		self.assertDictEqual(connection_info_api, connection_info_core)


	def test_topology_usage_non_existing_connection(self):
		"""
		tests wether connection usage for a non existing topology is responded correctly
		"""

		testtopology_id = self.testtopology_id[12:24] + self.testtopology_id[0:12]

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.topology_usage,
							   testtopology_id)

