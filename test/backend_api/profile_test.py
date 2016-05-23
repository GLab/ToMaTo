from proxies_test import ProxyHoldingTestCase, ProxyHolder
from lib.error import UserError
import unittest
import time

# the API tests assume that all other backend services work properly.

'''
covered API functions:
	profile_list
		Scenario 1: No parameters
		Scenario 2: Set tech parameter to existing technology
		Scenario 3: Set tech parameter to non existing technology
	profile_create
		Scenario 1: Correct parameters
		Scenario 2: Correct parameters, no permission
		Scenario 3: Non existing techs, and otherwise corret parameters
		Scenario 4: Already existing name (and same technology), but otherwise correct parameters
		Scenario 5: Incorrect attributes
	profile_modify
		Scenario 1: Correct parameters
		Scenario 2: Correct parameters, no permission
		Scenario 3: Non existing profile
		Scenario 4: Incorrect attributes
	profile_remove
		Scenario 1: Correct parameter
		Scenario 2: Correct parameter, no permission
		Scenario 3: Non existing profile
	profile_info
		Scenario 1: Correct parameters
		Scenario 2: Non existing id
'''

class ProfileTestCase(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_profiles()
		self.remove_all_other_accounts()

		#Create test profile for openvz
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
		self.testprofile_id = self.proxy_holder.backend_core.profile_id(self.testprofile_tech, self.testprofile_name)

	def tearDown(self):
		self.remove_all_profiles()
		self.remove_all_other_accounts()


	#Receive a list by calling profile_list() without any parameters and check correctness
	def test_profile_list_without_param(self):

		profile_list_api = self.proxy_holder.backend_api.profile_list()
		self.assertIsNotNone(profile_list_api)

		profile_list_core = self.proxy_holder.backend_core.profile_list()
		self.assertIsNotNone(profile_list_core)

		self.assertEqual(profile_list_api, profile_list_core)

	#Receive a list by calling profile_list() with testprofile technology as parameter and check correctness
	def test_profile_list_correct_param(self):


		profile_list_api = self.proxy_holder.backend_api.profile_list(self.testprofile_tech)
		self.assertIsNotNone(profile_list_api)

		profile_list_core = self.proxy_holder.backend_core.profile_list(self.testprofile_tech)
		self.assertIsNotNone(profile_list_core)

		self.assertEqual(profile_list_api, profile_list_core)

	#Receive a list by calling profile_list() with a non existing technology as parameter and check for emptiness
	def test_profile_list_non_existing(self):

		profile_tech = "closedvz"

		profile_list_api = self.proxy_holder.backend_api.profile_list(profile_tech)
		self.assertEqual(profile_list_api, [])
		profile_list_core = self.proxy_holder.backend_core.profile_list(profile_tech)
		self.assertEqual(profile_list_core, [])

	#Create a new correct profile
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

	#Create a new correct profile without the user permission to do so
	def test_profile_create_no_permission(self):
		#Valid profile
		profile_tech = "kvmqm"
		profile_name = "normal"
		profile_args = {'diskspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'preference': 10, 'description': 'Test profile'}

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.profile_create, profile_tech, profile_name, profile_args)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_core.profile_id, profile_tech, profile_name)

	#Create a new profile with non existing technology
	def test_profile_create_non_existing_tech(self):
		#Valid profile
		profile_tech = "not_existing"
		profile_name = "normal"
		profile_args = {'diskspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'preference': 10, 'description': 'Test profile'}

		self.assertRaisesError(UserError, UserError.INVALID_VALUE, self.proxy_holder.backend_api.profile_create, profile_tech, profile_name, profile_args)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.profile_id, profile_tech, profile_name)

	#Create a new profile which already exists (same technology and name)
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

	#Create a new profile with non existing attribute
	def test_profile_create_with_incorrect_attributes(self):
		#Valid profile
		profile_tech = "kvmqm"
		profile_name = "normal"
		profile_args = {'disksspace': 5120, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal', 'description': 'Test profile', 'preference': 10}

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.profile_create, profile_tech, profile_name, profile_args)

	#Modify the testprofile correctly
	def test_profile_modify(self):

		profile_args = self.testprofile_args

		#Modified attributes
		profile_args['diskspace'] = 5120
		profile_args['ram'] = 1024
		profile_args['cpus'] = 2.0


		profile_info = self.proxy_holder.backend_api.profile_info(self.testprofile_id)
		self.assertIsNotNone(profile_info)
		profile_modified = self.proxy_holder.backend_api.profile_modify(id=self.testprofile_id, attrs=profile_args)
		self.assertIsNotNone(profile_modified)
		self.assertNotEqual(profile_info, profile_modified)

		profile_info_core = self.proxy_holder.backend_core.profile_info(self.testprofile_id)
		self.assertEqual(profile_info_core, profile_modified)

	#Try to modify existing profile without user permission and check for correct response
	def test_profile_modify_without_permission(self):

		profile_args = self.testprofile_args

		#Modified attributes
		profile_args['diskspace'] = 5120
		profile_args['ram'] = 1024
		profile_args['cpus'] = 2.0

		profile_info = self.proxy_holder.backend_api.profile_info(self.testprofile_id)
		self.assertIsNotNone(profile_info)
		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.profile_modify, self.testprofile_id, profile_args)

		profile_info_core = self.proxy_holder.backend_core.profile_info(self.testprofile_id)
		self.assertEqual(profile_info_core, profile_info)

	#Modify a non existing profile and check for correct error
	def test_profile_modify_non_existing_profile(self):

		profile_args = self.testprofile_args

		#Modified attributes
		profile_args['diskspace'] = 5120
		profile_args['ram'] = 1024
		profile_args['cpus'] = 2.0


		#Creating non existing profile_id
		profile_id = self.testprofile_id + self.testprofile_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_modify, profile_id, profile_args)

	#Modify non existing attributes
	def test_profile_modify_incorrect_attributes(self):


		profile_args = self.testprofile_args
		profile_args["weight"] = 50


		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.profile_modify, self.testprofile_id, profile_args)


	#Remove an existing profile
	def test_profile_remove(self):
		self.proxy_holder.backend_api.profile_remove(self.testprofile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.profile_info, self.testprofile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_info, self.testprofile_id)

	#Try to remove an existing profile without permission and check for User.DENIED response
	def test_profile_remove_without_permission(self):

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.profile_remove, self.testprofile_id)

		profile_core = self.proxy_holder.backend_core.profile_info(self.testprofile_id)
		self.assertIsNotNone(profile_core)

		profile_api = self.proxy_holder.backend_api.profile_info(self.testprofile_id)
		self.assertIsNotNone(profile_api)

	#Try to remove a non existing profile
	def test_profile_remove_non_existing_profile(self):

		#Creating non existing profile_id
		profile_id = self.testprofile_id + self.testprofile_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_remove, profile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.profile_info, profile_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_info, profile_id)

	#Get info about the testprofile and check correctness
	def test_profile_info(self):


		profile_info_api = self.proxy_holder.backend_api.profile_info(self.testprofile_id)
		profile_info_core = self.proxy_holder.backend_core.profile_info(self.testprofile_id)

		self.assertEqual(profile_info_api, profile_info_core)

	#Try to get info about a non existing profile
	def test_profile_info_non_existing(self):

		#create non existing id
		profile_id = self.testprofile_id + self.testprofile_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.profile_info, profile_id)

def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(ProfileTestCase),
	])
