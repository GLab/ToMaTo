from proxies import ProxyHolder, ProxyHoldingTestCase
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
		self.testnetwork_kind = "internet"
		self.testnetwork_attrs = {
				'description': '',
				   'show_as_common': True,
				   'restricted': False,
				   'big_icon': True,
				   'label': 'Internet',
				   'preference': 100,
		}
		self.proxy_holder.backend_api.network_create(self.testnetwork_kind,self.testnetwork_attrs)
		self.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)

		self.testnetwork2_kind = "internet/small"
		self.testnetwork2_attrs = {
				'description': '',
				   'show_as_common': False,
				   'restricted': True,
				   'big_icon': True,
				   'label': 'Internet',
				   'preference': 50,
		}

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


	#Create a network with correct parameters
	def test_network_create(self):

		network_api = self.proxy_holder.backend_api.network_create(self.testnetwork2_kind, self.testnetwork2_attrs)
		self.assertIsNotNone(network_api)
		self.assertDictContainsSubset(self.testnetwork2_attrs, network_api)
		network_list_core = self.proxy_holder.backend_core.network_list()

		for network in network_list_core:
			if network['kind'] == self.testnetwork2_kind:
				self.assertDictContainsSubset(self.testnetwork2_attrs, network)

	#Create network without permission and check if backend denies
	def test_network_create_without_permission(self):

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.network_create, self.testnetwork2_kind, self.testnetwork2_attrs)

		network_list_core = self.proxy_holder.backend_core.network_list()

		for network in network_list_core:
			self.assertIsNot(network['kind'],self.testnetwork2_kind)

	#Try to create a network with incorrect parameters and check for correct backend response
	def test_network_create_with_incorrect_parameters(self):

		network_attrs = self.testnetwork2_attrs.copy()
		network_attrs['weight'] = 50

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.network_create, self.testnetwork2_kind, network_attrs)

	#Modify a network with valid parameters
	def test_network_modify(self):

		network_attrs = self.testnetwork_attrs.copy()
		network_attrs['preference'] == 50


		network_api = self.proxy_holder.backend_api.network_modify(self.testnetwork_id, network_attrs)
		self.assertIsNotNone(network_api)
		network_core = self.proxy_holder.backend_core.network_info(self.testnetwork_id)
		self.assertIsNotNone(network_core)
		self.assertDictContainsSubset(network_attrs, network_api)

	#Modify a network without permission and check if backend denies
	def test_network_create_without_permission(self):

		network_attrs = self.testnetwork_attrs.copy()
		network_attrs['preference'] == 50

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.network_modify, self.testnetwork_id, network_attrs)

		network_core = self.proxy_holder.backend_core.network_info(self.testnetwork_id)

		self.assertDictContainsSubset(self.testnetwork_attrs, network_core)


def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(NetworkTestCase),
	])