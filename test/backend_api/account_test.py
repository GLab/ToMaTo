#!/usr/bin/python

from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest

# the API tests assume that all other backend services work properly.

"""
### account_info
- Scenario 1: No username
- Scenario 2: Correct username (e.g. admin)
- Scenario 3: Incorrect username

### account_list
- Scenario 1: No parameters
- Scenario 2: Correct parameters
  - Scenario 2.1: Existing organisation
  - Scenario 2.2: Known flag  for existing user
  - Scenario 2.3: Existing organisation and given flag for a specific user
- Scenario 3: Incorrect parameters (using wrong parameter types)
- Scenario 4: Non existing organizations
- Scenario 5: Non existing flag

### account_modify
- Scenario 1: No parameters 
- Scenario 2: Correct parameters
  - Scenario 2.1: Correct name and existing attributes with correct content
  - Scenario 2.2: Correct name and existing attributes without permission to modify a single attribute and setting ignore_key_on_unauthorized to true
  - Scenario 2.3: Changing username to already existing username

- Scenario 3: Correct parameters, without permission
- Scenario 4: Incorrect parameters
  - Scenario 4.1: Incorrect name
  - Scenario 4.2: Non existing attributes
  - Scenario 4.3: Incorrect attributes
  - Scenario 4.4: Non existing references, like a imaginary organization
### account_create
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters, without permission
- Scenario 2: Incorrect parameters
  - Scenario 2.1: Already existing username
  - Scenario 2.2: No password
  - Scenario 2.3: Non existing organization
  - Scenario 2.4: Incorrect attributes
  - Scenario 2.5: Non existing attributes

### account_remove
- Scenario 1: Correct username
- Scenario 2: Correct parameters, without permission
- Scenario 2: No username
- Scenario 3: Incorrect username
- Scenario 4: Non existing username

### account_usage:
- Scenario 1: Correct username
- Scenario 2: Not existing username

## account_notification
### account_notifications
- Scenario 1: No parameters
- Scenario 2: include_read = true

### account_notification_set_read
- Scenario 1: Correct parameters
- Scenario 2: Not existing notification
- Scenario 3: Already flagged notification 

### account_send_notification
- May need better documentation
- Scenario 1: Correct parameters
- Scenario 2: Non existing user

### broadcast_announcement
- May also need better documentation
- Scenario 1: Correct parameters
- Scenario 3: show_sender=False

### notify_admins
- Scenario 1: Correct parameters
- Scenario 2: Global_contact = False
- Scenario 3: Global = False, "admin" = false

"""

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

class AccountListTestCases(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

		self.proxy_holder.backend_api.organization_create("DummyCorp1")
		self.proxy_holder.backend_api.organization_create("DummyCorp2")

		username = "testuser"
		password = "123"
		organization = "DummyCorp1"
		attrs = {
			"realname": "Test User",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

		username = "testuser2"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

	def tearDown(self):
		self.remove_all_other_accounts()
		self.remove_all_other_organizations()

	def test_account_list_none(self):
		"""
		tests whether account_list responds correctly when given no argument. Should return all accounts for current user=admin otherwise throw exception
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_list(),self.proxy_holder.backend_users.user_list())

		self.proxy_holder_tester = ProxyHolder("testuser","123")

		self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.account_list,[])

	def test_account_list_existing_orga(self):
		"""
		tests whether account_list correctly returns the user list of the given organization
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_list("DummyCorp1"),self.proxy_holder.backend_users.user_list("DummyCorp1"))

	def test_account_list_existing_orga_existing_flag(self):
		"""
		tests whether account_list correctly returns the user list of the given organization with given flag
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_list("DummyCorp1","over_quota"),self.proxy_holder.backend_users.user_list("DummyCorp1","over_quota"))

	def test_account_list_existing_orga_non_existing_flag(self):
		"""
		tests whether account_list correctly returns the user list of the given organization with given flag
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_list("DummyCorp1", "over_quotas"),[])

	def test_account_list_non_existent_orga(self):
		"""
		tests whether account_list responds correctly to non existent organization as argument
		"""
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.account_list, "NoCorp")

	def test_account_list_non_existent_flag(self):
		"""
		tests whether account_list responds correctly to non existent flag as argument
		"""
		self.assertEqual(self.proxy_holder.backend_api.account_list(None, "over_quotas"),[])

class AccountModifyTestCases(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

		self.proxy_holder.backend_api.organization_create("DummyCorp1")
		self.proxy_holder.backend_api.organization_create("DummyCorp2")

		username = "testuser"
		password = "123"
		organization = "DummyCorp1"
		attrs = {
			"realname": "Test User",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

		username = "testuser2"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester = ProxyHolder("testuser","123")

	def tearDown(self):
		self.remove_all_other_accounts()
		self.remove_all_other_organizations()

	def test_account_modify_none(self):
		"""
		tests whether account_modify correctly reacts, when given no parameters
		"""
		before = self.proxy_holder.backend_api.account_info()

		self.proxy_holder.backend_api.account_modify()

		after = self.proxy_holder.backend_api.account_info()

		self.assertEqual(before, after)

	def test_account_modify_correct(self):
		"""
		tests whether account_modify correctly modifies when given username and correct attributes
		"""
		before = self.proxy_holder.backend_api.account_info("testuser2")

		self.proxy_holder.backend_api.account_modify("testuser2",{"realname": "Test User2",
			"email": "test2@example.com",
			"flags": {"over_quota": True}})

		after = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertEqual(after["email"], "test2@example.com")

	def test_account_modify_correct_wo_permission(self):
		"""
		tests whether account_modify correctly modifies when given username and correct attributes but without permissions for all attributes and ignore_key=True
		"""
		before = self.proxy_holder.backend_api.account_info("testuser")

		self.proxy_holder_tester.backend_api.account_modify("testuser", {"realname": "Test User2",
			"email": "test2@example.com",
			"flags": {"over_quota": True}}, True,True)

		after = self.proxy_holder.backend_api.account_info("testuser")

		self.assertEqual(after["email"], "test2@example.com")

	def test_account_modify_correct_wo_permission_2(self):
		"""
		tests whether account_modify correctly modifies when given username and correct attributes but without permissions and ignore_key=False
		"""
		before = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.account_modify,"testuser2",{"realname": "Test User2",
			"email": "test2@example.com",
			"flags": {"over_quota": True}},False)

		after = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertEqual(after["email"], "test@example.com")

	def test_account_modify_to_already_existing_name(self):
		"""
		tests whether account_modify recognizes that username already exists
		"""
		before = self.proxy_holder.backend_api.account_info("testuser2")

		self.proxy_holder.backend_api.account_modify("testuser2",{"realname": "Test User",
			"email": "test2@example.com",
			"flags": {"over_quota": True}})

		after = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertEqual(after["realname"],"Test User")

	def test_account_modify_wrong_name(self):
		"""
		tests whether account_modify recognizes that name is not acceptable
		"""

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.account_modify,"testuser3",{"realname": "te",
			"email": "test2@example.com",
			"flags": {"over_quota": True}})

	def test_account_modify_non_existing_attribute(self):
		"""
		tests whether account_modify recognizes that attribute is not existent
		"""
		before = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder.backend_api.account_modify,"testuser2",{"realname": "test user",
			"gender": "transgender",
			"flags": {"over_quota": True}})

		after = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertEqual(after,before)

	def test_account_modify_wrong_attribute(self):
		"""
		tests whether account_modify recognizes that attribute is wrong
		"""
		before = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.account_modify,"testuser2",{"realname": "test user",
			"organization": "DummyCorp3",
			"flags": {"over_quota": True}})

		after = self.proxy_holder.backend_api.account_info("testuser2")

		self.assertEqual(after,before)

class AccountCreateTestCases(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

		self.proxy_holder.backend_api.organization_create("DummyCorp1")
		self.proxy_holder.backend_api.organization_create("DummyCorp2")

		username = "testuser"
		password = "123"
		organization = "DummyCorp1"
		attrs = {
			"realname": "Test User",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

		username = "testuser2"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester = ProxyHolder("testuser","123")

	def tearDown(self):
		self.remove_all_other_accounts()
		self.remove_all_other_organizations()

	def test_account_create_correct(self):
		"""
		tests whether account_create correctly works, when given correct parameters
		"""
		username = "testusercase"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}

		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

		self.assertIsNotNone(self.proxy_holder.backend_api.account_info("testusercase"))

	def test_account_create_correct_wo_permissions(self):
		"""
		tests whether account_create correctly works, when given correct parameters but without permissions
		"""
		username = "testusercase"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.account_create,username, password, organization, attrs)

	def test_account_create_existing_username(self):
		"""
		tests whether account_create correctly works, when given existing username
		"""
		username = "testuser"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}

		self.assertRaisesError(UserError, UserError.ALREADY_EXISTS, self.proxy_holder.backend_api.account_create,username, password, organization, attrs)

	def test_account_create_wo_password(self):
		"""
		tests whether account_create correctly works, when given no password
		"""
		username = "testuser3"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}

		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.assertIsNotNone(self.proxy_holder.backend_api.account_info("testuser3"))

	def test_account_create_non_ex_orga(self):
		"""
		tests whether account_create correctly works, when given non existing orga
		"""
		username = "testuser3"
		password = "123"
		organization = "NoCorp"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}

		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.account_create,username, password, organization, attrs)

	def test_account_create_non_existent_attrs(self):
		"""
		tests whether account_create correctly works, when given wrong attributes
		"""
		username = "testuser3"
		password = "123"
		organization = "NoCorp"
		attrs = {
			"realname": "Test User2",
			"race": "human",
			"flags": {"over_quota": True}
		}

		self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder.backend_api.account_create,username, password, organization, attrs)

class AccountRemoveTestCases(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

		self.proxy_holder.backend_api.organization_create("DummyCorp1")
		self.proxy_holder.backend_api.organization_create("DummyCorp2")

		username = "testuser"
		password = "123"
		organization = "DummyCorp1"
		attrs = {
			"realname": "Test User",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

		username = "testuser2"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester = ProxyHolder("testuser","123")

	def tearDown(self):
		self.remove_all_other_accounts()
		self.remove_all_other_organizations()

	def test_account_remove_correct(self):
		"""
		tests whether account_remove correctly works, when given correct parameters
		"""

		self.proxy_holder.backend_api.account_remove("testuser")

		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.account_info,"testuser")

	def test_account_remove_correct_wo_permissions(self):
		"""
		tests whether account_remove correctly works, when given correct parameters but without permissions
		"""

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.account_remove,"testuser2")

		self.assertIsNotNone(self.proxy_holder.backend_api.account_info("testuser2"))

	def test_account_remove_no_parameters(self):
		"""
		tests whether account_remove correctly works, when given no paramaeters
		"""

		self.proxy_holder_tester.backend_api.account_remove()

	def test_account_remove_wrong_username(self):
		"""
		tests whether account_remove correctly works, when given wrong username
		"""

		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.account_remove,"NoUser")

class AccountUsageTestCases(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

		self.proxy_holder.backend_api.organization_create("DummyCorp1")
		self.proxy_holder.backend_api.organization_create("DummyCorp2")

		username = "testuser"
		password = "123"
		organization = "DummyCorp1"
		attrs = {
			"realname": "Test User",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

		username = "testuser2"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester = ProxyHolder("testuser","123")

	def tearDown(self):
		self.remove_all_other_accounts()
		self.remove_all_other_organizations()

	def test_account_usage_correct(self):
		"""
		tests whether account_usage correctly works, when given correct parameters
		"""

		self.assertIsNotNone(self.proxy_holder.backend_api.account_usage("testuser"))

	def test_account_usage_non_existent_user(self):
		"""
		tests whether account_usage correctly works, when given non_existent_user
		"""

		self.assertIsNotNone(self.proxy_holder.backend_api.account_usage("NoUser"))

class AccountNotificationTestCases(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()

		self.proxy_holder.backend_api.organization_create("DummyCorp1")
		self.proxy_holder.backend_api.organization_create("DummyCorp2")

		username = "testuser"
		password = "123"
		organization = "DummyCorp1"
		attrs = {
			"realname": "Test User",
			"email": "s_schlosse10@cs.uni-kl.de",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)

		username = "testuser2"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester = ProxyHolder("testuser","123")

		username = "testuser3"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True,
					  "orga_admin_contact": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester_broadcast = ProxyHolder("testuser3","123")

		username = "testuser4"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True,
					  "global_admin_contact": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester_global_admin = ProxyHolder("testuser4","123")

		username = "testuser5"
		password = "123"
		organization = "DummyCorp1"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True,
					  "global_host_contact": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester_global_host = ProxyHolder("testuser5","123")

		username = "testuser6"
		password = "123"
		organization = "DummyCorp2"
		attrs = {
			"realname": "Test User2",
			"email": "test@example.com",
			"flags": {"over_quota": True,
					  "orga_host_contact": True}
		}
		self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
		self.proxy_holder_tester_orga_host = ProxyHolder("testuser6","123")

		self.proxy_holder.backend_api.account_send_notification("testuser", "test", "message")
		self.proxy_holder.backend_api.account_send_notification("testuser", "test2", "message2")

	def tearDown(self):
		self.remove_all_other_accounts()
		self.remove_all_other_organizations()

	def test_account_notification_correct(self):

		self.assertIsNotNone(self.proxy_holder_tester.backend_api.account_notifications())

	def test_account_send_notifcation_correct(self):
		self.proxy_holder.backend_api.account_send_notification("testuser", "test5", "message5")
		self.assertIsNotNone(self.proxy_holder_tester.backend_api.account_notifications())

	def test_account_send_notifcation_including_read(self):
		self.proxy_holder_tester.backend_api.account_notification_set_read(self.proxy_holder_tester.backend_api.account_notifications(True)[0]["id"], True)
		self.proxy_holder_tester.backend_api.account_notification_set_read(self.proxy_holder_tester.backend_api.account_notifications(True)[1]["id"], True)
		self.assertIsNotNone(self.proxy_holder_tester.backend_api.account_notifications(True))

	def test_account_send_notifcation_non_existing_user(self):
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.account_send_notification,"NoUser", "test", "message")

	def test_account_send_broadcast_correct(self):
		self.proxy_holder.backend_api.broadcast_announcement("Broadcast", "bcmessage")
		self.assertIsNotNone(self.proxy_holder_tester_broadcast.backend_api.account_notifications(True))

	def test_account_send_broadcast_show_no_sender(self):
		self.proxy_holder.backend_api.broadcast_announcement("Broadcast", "bcmessage",None,False)
		self.assertIsNone(self.proxy_holder_tester_broadcast.backend_api.account_notifications(True)[0]["sender"])

	def test_account_read_notifcation_correct(self):
		self.proxy_holder_tester.backend_api.account_notification_set_read(self.proxy_holder_tester.backend_api.account_notifications()[0]["id"], True)
		self.assertFalse(self.proxy_holder_tester.backend_api.account_notifications()[0]["read"])

	def test_account_read_notifcation_no_message(self):
		self.proxy_holder_tester.backend_api.account_notification_set_read(self.proxy_holder_tester.backend_api.account_notifications()[0]["id"], True)
		self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder_tester.backend_api.account_notification_set_read,"nomessage", True)

	def test_account_read_notifcation_already_read_message(self):
		self.proxy_holder_tester.backend_api.account_notification_set_read(self.proxy_holder_tester.backend_api.account_notifications()[0]["id"], True)
		self.proxy_holder_tester.backend_api.account_notification_set_read(self.proxy_holder_tester.backend_api.account_notifications(True)[0]["id"], True)

	def test_notifyAdmins_correct(self):
		self.proxy_holder.backend_api.notifyAdmins("NoSubject","NoText")
		msg_received = False

		for msg in self.proxy_holder_tester_global_admin.backend_api.account_notifications():
			if msg['title'] == "NoSubject":
				msg_received = True

		self.assertTrue(msg_received)

	def test_notifyAdmins_correct_not_global(self):
		self.proxy_holder_tester_global_admin.backend_api.notifyAdmins("NoSubject","NoText",False)
		msg_received = False

		for msg in self.proxy_holder_tester_broadcast.backend_api.account_notifications():
			if msg['title'] == "NoSubject":
				msg_received = True

		self.assertTrue(msg_received)

	def test_notifyAdmins_correct_not_global_not_admin(self):
		self.proxy_holder_tester_global_admin.backend_api.notifyAdmins("NoSubject","NoText",False,"notadmin")
		msg_received = False

		for msg in self.proxy_holder_tester_orga_host.backend_api.account_notifications():
			if msg['title'] == "NoSubject":
				msg_received = True

		self.assertTrue(msg_received)

		msg_received = False
		for msg in self.proxy_holder_tester_global_host.backend_api.account_notifications():
			if msg['title'] == "NoSubject":
				msg_received = True

		self.assertFalse(msg_received)


def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(NoOtherAccountTestCase),
		unittest.TestLoader().loadTestsFromTestCase(OtherAccountTestCase),
		unittest.TestLoader().loadTestsFromTestCase(AccountListTestCases),
		unittest.TestLoader().loadTestsFromTestCase(AccountModifyTestCases),
		unittest.TestLoader().loadTestsFromTestCase(AccountCreateTestCases),
		unittest.TestLoader().loadTestsFromTestCase(AccountRemoveTestCases),
		unittest.TestLoader().loadTestsFromTestCase(AccountUsageTestCases),
		unittest.TestLoader().loadTestsFromTestCase(AccountNotificationTestCases),
	])