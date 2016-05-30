#!/usr/bin/python

from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest

# the API tests assume that all other backend services work properly.

class SiteTestCases(ProxyHoldingTestCase):

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


    def test_site_create(self):
        """
        tests whether site create correctly creates a site when given correct parameters
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        self.assertIsNotNone(self.proxy_holder.backend_api.site_info("DummySite"))

    def test_site_create_wo_permissions(self):
        """
        tests whether site create correctly responds when executed without permission
        """

        self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.site_create,"DummySite", "DummyCorp1")
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.site_info,"DummySite")

    def test_site_create_existing_site(self):
        """
        tests whether site create correctly creates a site when given existing site name
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        self.assertRaisesError(UserError,UserError.ALREADY_EXISTS, self.proxy_holder.backend_api.site_create, "DummySite", "DummyCorp1")

    def test_site_create_wrong_parameter(self):
        """
        tests whether site create correctly reacts when given wrong parameter/non existing organization
        """

        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.site_create,"DummySite", "NoCorp")

    def test_site_info_correct(self):
        """
        tests whether site info correctly returns the site info of an existing site
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        self.assertEqual(self.proxy_holder.backend_api.site_info("DummySite"), self.proxy_holder.backend_core.site_info("DummySite"))

    def test_site_info_wrong_parameter(self):
        """
        tests whether site info correctly responds when giv
        en non existing site as parameter
        """

        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.site_info,"NoSite")

    def test_site_list_correct(self):
        """
        tests whether site list correctly returns all sites
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        self.assertEqual(self.proxy_holder.backend_api.site_list(), self.proxy_holder.backend_core.site_list())

    def test_site_list_existing_organization(self):
        """
        tests whether site list correctly returns the list of all sites for the given organization
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        self.assertEqual(self.proxy_holder.backend_api.site_list("DummyCorp1"), self.proxy_holder.backend_core.site_list("DummyCorp1"))

    def test_site_list_non_existing_organization(self):
        """
        tests whether site list correctly responds when given non existing organization as parameter
        """

        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.site_list,"NoCorp")

    def test_site_remove_correct(self):
        """
        tests whether site remove correctly removes a site
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        self.proxy_holder.backend_api.site_remove("DummySite")
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.site_info,"DummySite")

    def test_site_remove_non_existing_site(self):
        """
        tests whether site remove correctly responds when given a non existing site as parameter
        """

        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.site_info,"NoSite")

    def test_site_remove_without_permission(self):
        """
        tests whether site remove correctly reacts when called without permissions
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.site_remove,"DummySite")

    def test_site_modify_correct(self):
        """
        tests whether site modify correctly modifies the given site with the given parameters
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")

        attrs = {
            "label": "DummyLabel"
        }
        self.proxy_holder.backend_api.site_modify("DummySite",attrs)
        self.assertEqual(self.proxy_holder.backend_api.site_info("DummySite")["label"],"DummyLabel")

    def test_site_modify_correct_wo_permission(self):
        """
        tests whether site modify correctly responds when called without sufficient permissions
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")

        attrs = {
            "label": "DummyLabel"
        }
        self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.site_modify,"DummySite",attrs)

    def test_site_modify_non_existing_site(self):
        """
        tests whether site modify correctly responds when called with an unvalid site name
        """

        attrs = {
            "label": "DummyLabel"
        }
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.site_modify,"NoSite",attrs)

    def test_site_modify_wrong_parameters(self):
        """
        tests whether site modify correctly responds when called with an unvalid attribute as parameter
        """

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")

        attrs = {
            "NoAttribute": "DummyLabel"
        }
        self.assertRaisesError(UserError,UserError.UNSUPPORTED_ATTRIBUTE,self.proxy_holder.backend_api.site_modify,"DummySite",attrs)

class SiteTestCasesWithHost(ProxyHoldingTestCase):

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

        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp1")
        host_1 = self.test_host_addresses[0]
        self.add_host_if_missing(host_1)
        self.proxy_holder.backend_core.host_modify(self.get_host_name(host_1), {'site': "DummySite"})


    def tearDown(self):
        host_1 = self.test_host_addresses[0]
        self.remove_host_if_available(self.get_host_name(host_1))
        self.remove_all_other_accounts()
        self.remove_all_other_sites()
        self.remove_all_other_organizations()


    def test_site_remove_contains_hosts(self):
        """
        tests whether site remove correctly responds when called with a site as parameter that still contains hosts
        """
        self.assertRaisesError(UserError,UserError.NOT_EMPTY,self.proxy_holder.backend_api.site_remove,"DummySite")





def suite():
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(SiteTestCases)
    ])