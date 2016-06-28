from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class TopologyTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()

		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)

		cls.add_templates_if_missing()

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
		cls.proxy_holder.backend_users.organization_create("DummyCorp",label="DummyCorp")

		testuser_username = "testuser_admin"
		testuser_password = "123"
		testuser_organization = "DummyCorp"
		testuser_attrs = {"realname": "Test User Admin",
						  "email": "admin@example.com",
						  "flags": {
							  "global_admin": True,
							  "orga_admin": True,
							  "global_topl_owner": True,
							  "global_host_manager": True,
							  "debug": True
						  }
						  }
		cls.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization,
													testuser_attrs)
		cls.proxy_holder_admin = ProxyHolder(testuser_username, testuser_password)


	def setUp(self):
		self.testtopology = self.proxy_holder.backend_core.topology_create(self.default_user_name)
		self.testtopology_id = self.testtopology['id']


	def tearDown(self):
		self.remove_all_topologies()


	@classmethod
	def tearDownClass(cls):
		cls.remove_all_topologies()
		cls.remove_all_templates()
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
		self.assertEqual(self.proxy_holder_admin.backend_api.topology_list(full=True,organization="DummyCorp") ,
						 self.proxy_holder_admin.backend_core.topology_list(full=True,organization_filter="DummyCorp"))

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
