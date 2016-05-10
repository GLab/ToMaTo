from test.proxies import ProxyHoldingTestCase, ProxyHolder
from ..proxies import ProxyHolder, ProxyHoldingTestCase
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

class NoOtherAccountTestCase(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

	def tearDown(self):
		self.remove_all_other_accounts()

	def test_account_recognition(self):
		"""
		tests whether the correct account is recognized. assumes account_info is correct
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_info()['name'], self.proxy_holder.username)

	def test_account_info(self):
		"""
		tests whether account info is correct
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_info(self.proxy_holder.username),
		                 self.proxy_holder.backend_users.user_info(self.proxy_holder.username))

	def test_account_create(self):
		username = "testuser"
		password = "123"
		organization = self.default_organization_name
		attrs = {
			"realname": "Test User",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}

		ainf = self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.assertIsNotNone(ainf)
		real_ainf = self.proxy_holder.backend_users.user_info(username)
		self.assertEqual(ainf, real_ainf)

class OtherAccountTestCase(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

		self.testuser_username = "testuser"
		self.testuser_password = "123"
		self.testuser_organization = self.default_organization_name
		self.testuser_email = "test@example.com"
		self.testuser_realname = "Test User"
		self.testuser_flags = ["over_quota"]

		self.set_user(self.testuser_username, self.testuser_organization, self.testuser_email, self.testuser_password, self.testuser_realname, self.testuser_flags)

	def tearDown(self):
		self.remove_all_other_accounts()

	def test_account_remove(self):
		self.proxy_holder.backend_api.account_remove(self.testuser_username)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_users.user_info, self.testuser_username)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.account_info, self.testuser_username)


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


class TemplateTestCase(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_profiles()
		self.remove_all_other_accounts()

		#self.add_templates_if_missing()
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


		#Create template

		self.testtemplate_technology = "openvz"
		self.testtemplate_name = "ubuntu-14.04.2_x86_64"
		self.testtemplate_attrs = {'nlXTP_installed': True,
			 'description': '',
			 'icon': '',
			 'show_as_common': False,
			 'restricted': False,
			 'torrent_data': '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',
			 'label': 'Ubuntu 14.04 (x86_64)',
			 'subtype': 'linux',
			 'preference': 0,
			 'creation_date': time.time(),
			 }

		self.proxy_holder.backend_core.template_create(self.testtemplate_technology, self.testtemplate_name, self.testtemplate_attrs)
		self.testtemplate_id = self.proxy_holder.backend_core.template_id(tech=self.testtemplate_technology, name=self.testtemplate_name)


	def tearDown(self):
		self.remove_all_profiles()
		self.remove_all_other_accounts()
		self.remove_all_templates()


	def test_template_remove(self):

		self.proxy_holder.backend_api.template_remove(self.testtemplate_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.template_info, self.testtemplate_id)

def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(NoOtherAccountTestCase),
		unittest.TestLoader().loadTestsFromTestCase(OtherAccountTestCase),
		unittest.TestLoader().loadTestsFromTestCase(ProfileTestCase),
		unittest.TestLoader().loadTestsFromTestCase(TemplateTestCase),
	])
