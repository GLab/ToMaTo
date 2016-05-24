from proxies_test import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import time


'''
## network

'''


class NetworkTestCase(ProxyHoldingTestCase):

	def setUp(self):
		self.remove_all_other_accounts()
		self.remove_all_networks()

		#Create user without permission to create, remove or modify networks
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = self.default_organization_name
		testuser_attrs = {"realname": "Test User",
			"email": "test@example.com",
			"flags": {}
		}
		self.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization, testuser_attrs)
		self.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)


		#Create network
		testnetwork_kind = "'internet"
		testnetwork_attrs = {
				'description': '',
				   'show_as_common': True,
				   'restricted': False,
				   'big_icon': True,
				   'label': 'Internet',
				   'preference': 100,
		}
		self.proxy_holder.backend_api.network_create(testnetwork_kind,testnetwork_attrs)
		self.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)


		#Create template

		self.testnetwork_id = self.proxy_holder.backend_core.network_list()[0]['id']


	def tearDown(self):
		self.remove_all_other_accounts()
		self.remove_all_networks()

	#Get network_list and check for correctness
	def test_network_list(self):

		network_list_api = self.proxy_holder.backend_api.network_list()
		self.assertIsNotNone(network_list_api)
		network_list_core = self.proxy_holder.backend_core.network_list()
		self.assertIsNotNone(network_list_core)
		self.assertEqual(network_list_api, network_list_core)

	

def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(NetworkTestCase),
	])