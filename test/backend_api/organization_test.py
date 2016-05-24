#!/usr/bin/python

from proxies_test import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
from lib.hierarchy import ClassName
import unittest

# the API tests assume that all other backend services work properly.

class OrganizationTestCases(ProxyHoldingTestCase):

    def setUp(self):
        self.remove_all_other_accounts()
        self.remove_all_other_sites()
        self.remove_all_other_organizations()
        self.proxy_holder.backend_api.organization_create("DummyCorp1")

        username = "testuser"
        password = "123"
        organization = "DummyCorp1"
        attrs = {
        	"realname": "Test User",
        	"email": "s_schlosse10@cs.uni-kl.de",
        	"flags": {"over_quota": True}
        }
        self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
        self.proxy_holder_tester = ProxyHolder("testuser","123")


    def tearDown(self):
        self.remove_all_other_accounts()
        self.remove_all_other_sites()
        self.remove_all_other_organizations()


    def test_organization_create(self):
        """
        tests whether organization create correctly creates an organization when given correct parameters
        """

        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.assertIsNotNone(self.proxy_holder.backend_api.organization_info("DummyCorp"))

    def test_organization_create_wo_permission(self):
        """
        tests whether organization create correctly creates an organization when given correct parameters but without permissions
        """

        self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.organization_create,"DummyCorp")

    def test_organization_create_duplicate(self):
        """
        tests whether organization create correctly raises an error when user tries to create duplicate organization
        """
        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.assertRaisesError(UserError,UserError.ALREADY_EXISTS,self.proxy_holder.backend_api.organization_create,"DummyCorp")

    def test_organization_info_correct(self):
        """
        tests whether organization info correctly works when given correct parameter
        """
        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.assertIsNotNone(self.proxy_holder.backend_api.organization_info("DummyCorp"))
        self.assertEqual(self.proxy_holder.backend_api.organization_info("DummyCorp"), self.proxy_holder.backend_users.organization_info("DummyCorp"))

    def test_organization_info_wrong_parameter(self):
        """
        tests whether organization info correctly works when given false parameter
        """
        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.organization_info, "NoCorp")

    def test_organization_modify_correct_parameter(self):
        """
        tests whether organization modify correctly works when given correct parameter
        """
        attrs = {
            "label": "DC1"
        }
        self.proxy_holder.backend_api.organization_modify("DummyCorp1", attrs)
        self.assertEqual(self.proxy_holder.backend_api.organization_info("DummyCorp1")["label"], "DC1")

    def test_organization_modify_correct_parameter_wo_permission(self):
        """
        tests whether organization modify correctly works when given correct parameter but without permission
        """
        attrs = {
            "label": "DC1"
        }
        self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.organization_modify,"DummyCorp1", attrs)
        self.assertEqual(self.proxy_holder.backend_api.organization_info("DummyCorp1")["label"], "DummyCorp1")

    def test_organization_modify_wrong_parameter(self):
        """
        tests whether organization modify correctly works when given wrong parameter/non existing organization
        """
        attrs = {
            "label": "DC1"
        }
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.organization_modify,"NoCorp", attrs)

    def test_organization_remove(self):
        """
        tests whether organization remove correctly removes an organization when given correct parameters
        """

        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.proxy_holder.backend_api.organization_remove("DummyCorp")
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.organization_info,"DummyCorp")

    def test_organization_remove_wo_permissions(self):
        """
        tests whether organization remove correctly responds when trying to remove an organization without permissions
        """

        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.organization_remove,"DummyCorp")

    def test_organization_remove_wrong_parameters(self):
        """
        tests whether organization remove correctly responds when given false parameters/non existing organization
        """
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.organization_info,"NoCorp")

    def test_organization_remove_remaining_sites(self):
        """
        tests whether organization remove correctly responds when given false parameters/still remaining sites
        """
        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.proxy_holder.backend_api.site_create("DummySite","DummyCorp")

        self.assertRaisesError(UserError,UserError.NOT_EMPTY, self.proxy_holder.backend_api.organization_remove,"DummyCorp")

    def test_organization_usage_correct(self):
        """
        tests whether organization usage correctly responds when given correct parameters
        """
        # Nothing to test yet
        #self.assertEqual(self.proxy_holder.backend_accounting.get_record(ClassName.ORGANIZATION, "DummyCorp1"), self.proxy_holder.backend_api.organization_usage("DummyCorp1"))
        #self.proxy_holder.backend_accounting.get_record(ClassName.ORGANIZATION, "DummyCorp1")

def suite():
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(OrganizationTestCases)
    ])