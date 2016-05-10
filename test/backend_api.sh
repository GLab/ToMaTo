from proxies import ProxyHoldingTestCase
from proxies import ProxyHolder
from lib.error import UserError
from .backend_api import account, organization
import unittest

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

	def test_account_info_no_argument(self):
		"""
		tests whether account_info responds correctly when given no username. Should return current user info
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_info(),self.proxy_holder.backend_api.account_info(self.proxy_holder.username))

	def test_account_info_non_existent_username(self):
		"""
		tests whether account_info responds correctly when given non existent username. Should raise exception
		"""
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.account_info, "NoUser")

	def test_account_info_for_self(self):
		"""
		tests whether account info is correct for self (i.e., includes everything)
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




def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(NoOtherAccountTestCase),
		unittest.TestLoader().loadTestsFromTestCase(OtherAccountTestCase),
		unittest.TestLoader().loadTestsFromTestCase(account.AccountListTestCases),
		unittest.TestLoader().loadTestsFromTestCase(account.AccountModifyTestCases),
		unittest.TestLoader().loadTestsFromTestCase(account.AccountCreateTestCases),
		unittest.TestLoader().loadTestsFromTestCase(account.AccountRemoveTestCases),
		unittest.TestLoader().loadTestsFromTestCase(account.AccountUsageTestCases),
		unittest.TestLoader().loadTestsFromTestCase(account.AccountNotificationTestCases),
	])