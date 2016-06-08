#!/usr/bin/python

from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError, TransportError,NetworkError
import unittest

# the API tests assume that all other backend services work properly.
"""
host_remove
- Scenario 3 in elements_test
"""


class HostTestCases(ProxyHoldingTestCase):

    def setUp(self):
        self.remove_all_other_accounts()
        self.remove_all_other_sites()
        self.remove_all_other_organizations()
        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp")
        self.address = self.test_host_addresses[0]

        username = "testuser"
        password = "123"
        organization = "DummyCorp"
        attrs = {
        	"realname": "Test User",
        	"email": "test@tester.de",
        	"flags": {"over_quota": True}
        }
        self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
        self.proxy_holder_tester = ProxyHolder("testuser","123")


    def tearDown(self):
        self.remove_all_hosts()
        #self.proxy_holder.backend_api.host_remove("DummyHost")
        self.remove_all_other_accounts()
        self.remove_all_other_sites()
        self.remove_all_other_organizations()


    def test_host_create(self):
        """
        tests whether host create correctly creates a host when given correct parameters
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())
        self.proxy_holder.backend_api.host_create("DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address,
            'address': self.address
            })
        self.assertIsNotNone(self.proxy_holder.backend_core.host_info("DummyHost"))

    def test_host_create_wo_permissions(self):
        """
        tests whether host create correctly responds when called without sufficient permissions
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())
        self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.host_create,"DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address,
            'address': self.address
            })

    def test_host_create_wo_attrs(self):
        """
        tests whether host create correctly responds when called without attributes
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())
        self.assertRaisesError(UserError,UserError.INVALID_CONFIGURATION,self.proxy_holder.backend_api.host_create,"DummyHost","DummySite")

    def test_host_create_existing_name(self):
        """
        tests whether host create correctly responds when called with non unique name
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())
        self.proxy_holder.backend_api.host_create("DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address,
            'address': self.address
            })
        self.assertRaisesError(UserError,UserError.ALREADY_EXISTS,self.proxy_holder.backend_api.host_create,"DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address,
            'address': self.address
            })

    def test_host_create_non_existing_site(self):
        """
        tests whether host create correctly responds when called with a non existing site
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.host_create,"DummyHost","NoSite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address,
            'address': self.address
            })

    def test_host_create_wrong_attrs(self):
        """
        tests whether host create correctly responds when called with a non existing attribute key
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())
        self.assertRaisesError(UserError,UserError.UNSUPPORTED_ATTRIBUTE,self.proxy_holder.backend_api.host_create,"DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address,
            'address': self.address,
            'nokey': "ThrowError"
            })

    def test_host_create_missing_attrs(self):
        """
        tests whether host create correctly responds when called with a missing attribute key
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())
        self.assertRaisesError(UserError,UserError.INVALID_CONFIGURATION,self.proxy_holder.backend_api.host_create,"DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address
            })

    @unittest.skip("Takes too long (1800s timeout)")
    def test_host_create_not_existing_host(self):
        """
        tests whether host create correctly responds when called without an existing host as parameter
        """
        self.assertEqual([],self.proxy_holder.backend_core.host_list())

        self.assertRaisesError(TransportError, "network.connect", self.proxy_holder.backend_api.host_create,"DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%"120.0.0.1",
            'address': "120.0.0.1"
            })


class HostTestCasesExistingHosts(ProxyHoldingTestCase):

    def setUp(self):
        self.remove_all_hosts()
        self.remove_all_other_accounts()
        self.remove_all_other_sites()
        self.remove_all_other_organizations()
        self.proxy_holder.backend_api.organization_create("DummyCorp")
        self.proxy_holder.backend_api.site_create("DummySite", "DummyCorp")
        self.address = self.test_host_addresses[0]

        self.proxy_holder.backend_api.host_create("DummyHost","DummySite",{
            'rpcurl': "ssl+jsonrpc://%s:8003"%self.address,
            'address': self.address
            })

        username = "testuser"
        password = "123"
        organization = "DummyCorp"
        attrs = {
        	"realname": "Test User",
        	"email": "test@tester.de",
        	"flags": {"over_quota": True}
        }
        self.proxy_holder.backend_api.account_create(username, password, organization, attrs)
        self.proxy_holder_tester = ProxyHolder("testuser","123")

    def tearDown(self):
        self.remove_all_hosts()
        self.remove_all_other_accounts()
        self.remove_all_other_sites()
        self.remove_all_other_organizations()

    def test_host_list_correct(self):
        """
        tests whether host_list() returns the same in the api as in the core.host_list()
        """
        self.assertEqual(self.proxy_holder.backend_api.host_list(),self.proxy_holder.backend_core.host_list() )

    def test_host_list_correct_with_site(self):
        """
        tests whether host_list(site) returns the same in the api as in the core.host_list(site)
        """
        self.assertEqual(self.proxy_holder.backend_api.host_list("DummySite"),self.proxy_holder.backend_core.host_list("DummySite") )
        self.assertIsNotNone(self.proxy_holder.backend_api.host_list("DummySite"))
        self.assertNotEqual([], self.proxy_holder.backend_api.host_list("DummySite"))

    def test_host_list_correct_with_orga(self):
        """
        tests whether host_list(None,orga) returns the same in the api as in the core.host_list(None,orga)
        """
        self.assertEqual(self.proxy_holder.backend_api.host_list(None,"DummyCorp"),self.proxy_holder.backend_core.host_list(None,"DummyCorp") )
        self.assertIsNotNone(self.proxy_holder.backend_api.host_list(None,"DummyCorp"))
        self.assertNotEqual([], self.proxy_holder.backend_api.host_list(None,"DummyCorp"))

    def test_host_list_correct_with_orga_and_site(self):
        """
        tests whether host_list(site,orga) returns the same in the api as in the core.host_list(site,orga)
        """
        self.assertEqual(self.proxy_holder.backend_api.host_list("DummySite","DummyCorp"),self.proxy_holder.backend_core.host_list("DummySite","DummyCorp") )
        self.assertIsNotNone(self.proxy_holder.backend_api.host_list("DummySite","DummyCorp"))
        self.assertNotEqual([], self.proxy_holder.backend_api.host_list("DummySite","DummyCorp"))

    def test_host_list_wrong_site(self):
        """
        tests whether host_list(site) reacts correctly when given a non existing site as parameter
        """
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.host_list,"NoSite")

    def test_host_list_wrong_site(self):
        """
        tests whether host_list(None,orga) reacts correctly when given a non existing orga as parameter
        """
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.host_list,None,"NoCorp")

    def test_host_info_correct(self):
        """
        tests whether host_info correctly return the host_info object when called with an existing host
        """
        self.assertEqual(self.proxy_holder.backend_api.host_info("DummyHost"), self.proxy_holder.backend_core.host_info("DummyHost"))

    def test_host_info_non_existing_host(self):
        """
        tests whether host_info correctly responds when called with a non existing host as parameter
        """
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.host_info,"NoHost")

    def test_host_modify_correct(self):
        """
        tests whether host_modify correctly modifys the host with the given name and with correct attributes
        """
        name="DummyHost"
        attrs={
            "name": "MyDummyHost"
        }
        self.proxy_holder.backend_api.host_modify(name,attrs)
        self.assertIsNotNone(self.proxy_holder.backend_api.host_info("MyDummyHost"))

    def test_host_modify_correct_wo_permissions(self):
        """
        tests whether host_modify correctly reacts when called without sufficient permissions
        """
        name="DummyHost"
        attrs={
            "name": "MyDummyHost"
        }
        self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.host_modify,name,attrs)

    def test_host_modify_wrong_attributes(self):
        """
        tests whether host_modify correctly reacts when called with wrong attributes
        """
        name="DummyHost"
        attrs={
            "name": "MyDummyHost",
            "nokey": "ThrowError"
        }
        self.assertRaisesError(UserError,UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.host_modify,name,attrs)

    def test_host_modify_non_existing_host(self):
        """
        tests whether host_modify correctly reacts when called with a non existing host
        """
        name="NoHost"
        attrs={
            "name": "MyDummyHost"
        }
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.host_modify,name,attrs)

    def test_host_remove_correct(self):
        """
        tests whether host_remove correctly removes the host with the provided name
        """
        self.proxy_holder.backend_api.host_remove("DummyHost")
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_core.host_info,"DummyHost")

    def test_host_remove_wo_permissions(self):
        """
        tests whether host_remove correctly responds when called without sufficient permissions
        """
        self.assertRaisesError(UserError,UserError.DENIED,self.proxy_holder_tester.backend_api.host_remove,"DummyHost")

    def test_host_remove_non_existing_host(self):
        """
        tests whether host_remove correctly responds when called without a non existing host as parameter
        """
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.host_remove,"NoHost")

    def test_host_users_host_wo_users(self):
        """
        tests whether host_users correctly returns an empty list if no users are using the host
        """
        self.assertEqual(self.proxy_holder.backend_api.host_users("DummyHost"),self.proxy_holder.backend_core.host_users("DummyHost"))
        self.assertEqual([],self.proxy_holder.backend_api.host_users("DummyHost"))

    def test_host_users_correct_wo_permissions(self):
        """
        tests whether host_users correctly responds when called without sufficient permissions
        """
        self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.host_users,"DummyHost")

    def test_host_users_non_existing_host(self):
        """
        tests whether host_users() responds correcty when called with a non existing host as parameter
        """
        self.assertRaisesError(UserError,UserError.ENTITY_DOES_NOT_EXIST,self.proxy_holder.backend_api.host_users,"NoHost")




def suite():
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(HostTestCases),
        unittest.TestLoader().loadTestsFromTestCase(HostTestCasesExistingHosts)
    ])
