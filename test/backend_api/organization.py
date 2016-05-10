#!/usr/bin/python

from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest

# the API tests assume that all other backend services work properly.

class OrganizationTestCases(ProxyHoldingTestCase):

    def setUp(self):
        self.remove_all_other_accounts()
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
        self.remove_all_other_organizations()

    def test_organization_create(self):
        """
        tests whether organization create correctly creates an organization when given correct parameters
        """

        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.assertIsNotNone(self.proxy_holder.backend_api.organization_list())

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

    def test_organization_info_wrong_parameter(self):
        """
        tests whether organization info correctly works when given false parameter
        """
        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.organization_info, "NoCorp")


def suite():
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(OrganizationTestCases)
    ])