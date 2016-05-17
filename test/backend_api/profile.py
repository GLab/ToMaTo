from proxies import ProxyHoldingTestCase, ProxyHolder
from lib.error import UserError
import unittest
import time

# the API tests assume that all other backend services work properly.

# covered API functions:
#  account
#   account_info
#     no argument
#     logged-in user
#   account_create
#     correct data
#   account_remove

class ProfileTestCase(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_profiles()
		self.remove_all_other_accounts()

		self.testprofile_tech = "openvz"
		self.testprofile_name = "normal"
		self.testprofile_args = {'diskspace': 10240, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'preference': 10, 'description': 'Test profile'}

		#Create user without permission to create profiles
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = self.default_organization_name
		testuser_attrs = {"realname": "Test User",
			"email": "test@example.com",
			"flags": {}
		}
		self.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization, testuser_attrs)
		self.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)


		self.proxy_holder.backend_core.profile_create(self.testprofile_tech,self.testprofile_name, self.testprofile_args)
		self.textprofile_id = self.proxy_holder.backend_core.profile_id(self.testprofile_tech, self.testprofile_name)

	def tearDown(self):
		self.remove_all_profiles()
		self.remove_all_other_accounts()


	def test_profile_list_without_param(self):

		profile_list_api = self.proxy_holder.backend_api.profile_list()
		self.assertIsNotNone(profile_list_api)

		profile_list_core = self.proxy_holder.backend_core.profile_list()
		self.assertIsNotNone(profile_list_core)

		self.assertEqual(profile_list_api, profile_list_core)

	def test_profile_list_correct_param(self):

		profile_tech = "openvz"

		profile_list_api = self.proxy_holder.backend_api.profile_list(profile_tech)
		self.assertIsNotNone(profile_list_api)

		profile_list_core = self.proxy_holder.backend_core.profile_list(profile_tech)
		self.assertIsNotNone(profile_list_core)

		self.assertEqual(profile_list_api, profile_list_core)

	def test_profile_list_non_existing(self):

		profile_tech = "closedvz"

		profile_list_api = self.proxy_holder.backend_api.profile_list(profile_tech)
		self.assertEqual(profile_list_api, [])
		profile_list_core = self.proxy_holder.backend_core.profile_list(profile_tech)
		self.assertEqual(profile_list_core, [])


	def test_profile_create(self):
		profile_tech = "kvmqm"
		profile_name = "normal"
		profile_args = {'diskspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'preference': 10, 'description': 'Test profile'}


		profile = self.proxy_holder.backend_api.profile_create(profile_tech, profile_name, profile_args)
		self.assertIsNotNone(profile)
		profile_id = self.proxy_holder.backend_core.profile_id(profile_tech, profile_name)
		self.assertIsNotNone(profile_id)
		ref_profile = self.proxy_holder.backend_core.profile_info(profile_id)
		self.assertEqual(profile, ref_profile)

	def test_profile_create_no_permission(self):
		#Valid profile
		profile_tech = "kvmqm"
		profile_name = "normal"
		profile_args = {'diskspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'preference': 10, 'description': 'Test profile'}

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.profile_create, profile_tech, profile_name, profile_args)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_core.profile_id,profile_tech, profile_name)

	def test_profile_create_non_existing_tech(self):
		#Valid profile
		profile_tech = "not_existing"
		profile_name = "normal"
		profile_args = {'diskspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'preference': 10, 'description': 'Test profile'}

		self.assertRaisesError(UserError, UserError.INVALID_VALUE, self.proxy_holder.backend_api.profile_create, profile_tech, profile_name, profile_args)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.profile_id, profile_tech, profile_name)

	def test_profile_create_already_existing(self):
		#Valid profile
		profile_tech = "kvmqm"
		profile_name = "normal"
		profile_args = {'diskspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'preference': 10, 'description': 'Test profile'}

		profile = self.proxy_holder.backend_api.profile_create(profile_tech, profile_name, profile_args)

		self.assertIsNotNone(profile)
		self.assertRaisesError(UserError, UserError.ALREADY_EXISTS, self.proxy_holder.backend_api.profile_create, profile_tech, profile_name, profile_args)
		profile_id_core = self.proxy_holder.backend_core.profile_id(profile_tech, profile_name)
		self.assertIsNotNone(profile_id_core)

	def test_profile_create_with_incorrect_attributes(self):
		#Valid profile
		profile_tech = "kvmqm"
		profile_name = "normal"
		profile_args = {'disksspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'description': 'Test profile', 'preference': 10}

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.profile_create, profile_tech, profile_name, profile_args)


	def test_profile_modify(self):

		profile_args = self.testprofile_args

		#Modified attributes
		profile_args['diskspace'] = 5120
		profile_args['ram'] = 1024
		profile_args['cpus'] = 2.0


		profile_info = self.proxy_holder.backend_api.profile_info(self.textprofile_id)
		self.assertIsNotNone(profile_info)
		profile_modified = self.proxy_holder.backend_api.profile_modify(id=self.textprofile_id, attrs=profile_args)
		self.assertIsNotNone(profile_modified)
		self.assertNotEqual(profile_info, profile_modified)

		profile_info_core = self.proxy_holder.backend_core.profile_info(self.textprofile_id)
		self.assertEqual(profile_info_core, profile_modified)

	def test_profile_modify_without_permission(self):

		profile_args = self.testprofile_args

		#Modified attributes
		profile_args['diskspace'] = 5120
		profile_args['ram'] = 1024
		profile_args['cpus'] = 2.0

		profile_info = self.proxy_holder.backend_api.profile_info(self.textprofile_id)
		self.assertIsNotNone(profile_info)
		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.profile_modify, self.textprofile_id, profile_args)

		profile_info_core = self.proxy_holder.backend_core.profile_info(self.textprofile_id)
		self.assertEqual(profile_info_core, profile_info)

	def test_profile_modify_non_existing_profile(self):

		profile_args = self.testprofile_args

		#Modified attributes
		profile_args['diskspace'] = 5120
		profile_args['ram'] = 1024
		profile_args['cpus'] = 2.0


		#Creating non existing profile_id
		profile_id = self.textprofile_id + self.textprofile_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_modify, profile_id, profile_args)

	def test_profile_modify_incorrect_attributes(self):


		profile_args = self.testprofile_args
		profile_args["weight"] = 50


		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.profile_modify, self.textprofile_id, profile_args)


	def test_profile_remove(self):
		self.proxy_holder.backend_api.profile_remove(self.textprofile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.profile_info, self.textprofile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_info, self.textprofile_id)

	def test_profile_remove_without_permission(self):

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.profile_remove, self.textprofile_id)

		profile_core = self.proxy_holder.backend_core.profile_info(self.textprofile_id)
		self.assertIsNotNone(profile_core)

		profile_api = self.proxy_holder.backend_api.profile_info(self.textprofile_id)
		self.assertIsNotNone(profile_api)

	def test_profile_remove_non_existing_profile(self):

		#Creating non existing profile_id
		profile_id = self.textprofile_id + self.textprofile_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_remove, profile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.profile_info, profile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_info, profile_id)

	def test_profile_info(self):


		profile_info_api = self.proxy_holder.backend_api.profile_info(self.textprofile_id)
		profile_info_core = self.proxy_holder.backend_core.profile_info(self.textprofile_id)

		self.assertEqual(profile_info_api, profile_info_core)


	def test_profile_info(self):


		profile_id = self.textprofile_id + self.textprofile_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_info,profile_id)

def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(ProfileTestCase),
	])
