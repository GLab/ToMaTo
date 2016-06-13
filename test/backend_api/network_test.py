from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import time


'''
##network
### network_list
- Execute and check for correctness

## network_create
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters without permissions
- Scenario 3: Invalid attributes

## network_modify
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters without permission
- Scenario 3: Non existing network
- Scenario 5: Incorrect attribute modification

## network_remove
- Scenario 1: Correct parameter
- Scenario 2: Correct parameters without permissions
- Scenario 3: Non existing network
- Scenario 4: Remove existing network with existing network instances

## network_info
- Scenario 1: Correct parameter
- Scenario 2: Non existing network
'''


class NetworkTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_other_accounts()


		# Create user without permission to create, remove or modify networks
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = cls.default_organization_name
		testuser_attrs = {"realname": "Test User",
						  "email": "test@example.com",
						  "flags": {}
						  }
		cls.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization,
													 testuser_attrs)
		cls.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)

	def setUp(self):
		self.remove_all_network_instances()
		self.remove_all_networks()

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

	@classmethod
	def tearDownClass(cls):
		cls.remove_all_other_accounts()

	def tearDown(self):
		self.remove_all_network_instances()
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
	def test_network_modify_without_permission(self):

		network_attrs = self.testnetwork_attrs.copy()
		network_attrs['preference'] == 50

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.network_modify, self.testnetwork_id, network_attrs)

		network_core = self.proxy_holder.backend_core.network_info(self.testnetwork_id)

		self.assertDictContainsSubset(self.testnetwork_attrs, network_core)

	#Modify incorrect attribute of existing network
	def test_network_modify_with_incorrect_attributes(self):

		network_attrs = self.testnetwork_attrs.copy()
		#Use non existing attribute
		network_attrs['weight'] = 50

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.network_modify, self.testnetwork_id, network_attrs)

		network_core = self.proxy_holder.backend_core.network_info(self.testnetwork_id)

		self.assertDictContainsSubset(self.testnetwork_attrs, network_core)

	#Modify non existing network
	def test_network_modify_non_existing_network(self):

		network_attrs = self.testnetwork_attrs.copy()
		network_attrs['preference'] == 50

		network_id = self.testnetwork_id + self.testnetwork_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_modify, network_id, network_attrs)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.network_info, network_id)


	#Remove existing network
	def test_network_remove(self):

		self.proxy_holder.backend_api.network_remove(self.testnetwork_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.network_info, self.testnetwork_id)


	#Try removing existing network without the correct permission
	def test_network_remove_without_permission(self):

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.network_remove, self.testnetwork_id)
		network_core = self.proxy_holder.backend_core.network_info(self.testnetwork_id)

		self.assertIsNotNone(network_core)

	#Try to remove non existing network
	def test_network_remove_non_existing(self):

		network_id = self.testnetwork_id + self.testnetwork_id
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_remove, network_id)


	#Get informations about existing element
	def test_network_info(self):
		network_api = self.proxy_holder.backend_api.network_info(self.testnetwork_id)
		network_core = self.proxy_holder.backend_core.network_info(self.testnetwork_id)
		self.assertEqual(network_api, network_core)
		self.assertDictContainsSubset(network_api, self.testnetwork_attrs)

	#Get informations about non existing element
	def test_network_info(self):

		network_id = self.testnetwork_id + self.testnetwork_id
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_info, network_id)


class NetworkTestWithHosts(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()
		#We need some hosts to test our network instances
		print cls.test_host_addresses
		for host_address in cls.test_host_addresses:
			cls.add_host_if_missing(host_address)

		#Create user without permission to create, remove or modify networks
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = cls.default_organization_name
		testuser_attrs = {"realname": "Test User",
			"email": "test@example.com",
			"flags": {}
		}
		cls.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization, testuser_attrs)
		cls.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)



	def setUp(self):
		self.remove_all_network_instances()
		self.remove_all_networks()

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

	@classmethod
	def tearDownClass(cls):
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()
		cls.remove_all_other_sites()

	def tearDown(self):
		self.remove_all_network_instances()
		self.remove_all_networks()



	def test_network_modify_change_kind_with_existing_instances(self):

		#Create a valid network instance
		testnetwork_instance_network = self.testnetwork_kind
		testnetwork_instance_host = self.get_host_name(self.test_host_addresses[0])
		testnetwork_instance_attrs = {'bridge': 'vmbr0'}

		self.proxy_holder.backend_api.network_instance_create(testnetwork_instance_network, testnetwork_instance_host, testnetwork_instance_attrs)
		testnetwork_instance_id = self.proxy_holder.backend_api.network_instance_list()[0]['id']

		#Now modify some attrs of our test network and check if the changed name concatenates automatically
		network_attrs = self.testnetwork_attrs.copy()
		network_attrs['kind'] = self.testnetwork_kind+self.testnetwork_kind

		network_api = self.proxy_holder.backend_api.network_modify(self.testnetwork_id, network_attrs)
		self.assertDictContainsSubset(network_attrs, network_api)

		network_core = self.proxy_holder.backend_core.network_modify(self.testnetwork_id, network_attrs)
		self.assertDictContainsSubset(network_attrs, network_core)

		network_instance_api = self.proxy_holder.backend_api.network_instance_info(testnetwork_instance_id)

		self.assertEqual(network_instance_api['network'], network_attrs['kind'])

	#Try to remove existing network with existing network_instances
	def test_network_remove_existing_network_with_instances(self):

		testnetwork_instance_network = self.testnetwork_kind
		testnetwork_instance_host = self.get_host_name(self.test_host_addresses[0])
		testnetwork_instance_attrs = {'bridge': 'vmbr0'}

		self.proxy_holder.backend_api.network_instance_create(testnetwork_instance_network, testnetwork_instance_host, testnetwork_instance_attrs)
		self.assertRaisesError(UserError, UserError.NOT_EMPTY,	self.proxy_holder.backend_api.network_remove, self.testnetwork_id)


'''
## network_instance
### network_instance_list
- Scenario 1: No parameters
- Scenario 2: With network parameter
- Scenario 3: With host parameter
- Scenario 4: With both parameters
- Scenario 5: Non existing parameter / host

### network_instance_create
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters, without permission
- Scenario 3: Non existing network
- Scenario 4: Non existing host

### network_instance_modify
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters, without permission
- Scenario 3: Non existing network instance
- Scenario 4: Incorrect attributes
- Scenario 5: Non existing host
- Scenario 6: Non existing network

### network_instance_remove
- Scenario 1: Correct parameter
- Scenario 2: Correct parameter, without permission
- Scenario 3: non existing network instance

### network_instance_info
- Scenario 1: Correct parameter
- Scenario 2: Non existing network instance
'''

class NetworkInstanceTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()
		# We need some hosts to test our network instances
		for host_address in cls.test_host_addresses:
			cls.add_host_if_missing(host_address)

		# Create user without permission to create, remove or modify networks
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = cls.default_organization_name
		testuser_attrs = {"realname": "Test User",
						  "email": "test@example.com",
						  "flags": {}
						  }
		cls.proxy_holder.backend_api.account_create(testuser_username, testuser_password, testuser_organization,
													 testuser_attrs)
		cls.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)


	def setUp(self):
		self.remove_all_network_instances()
		self.remove_all_networks()

		#Create network
		self.testnetwork_network = "internet"
		self.testnetwork_attrs = {
				'description': '',
				   'show_as_common': True,
				   'restricted': False,
				   'big_icon': True,
				   'label': 'Internet',
				   'preference': 100,
		}
		#Create network
		self.testnetwork2_network = "internet/TU"
		self.testnetwork2_attrs = {
				'description': '',
				   'show_as_common': False,
				   'restricted': False,
				   'big_icon': True,
				   'label': 'Internet',
				   'preference': 90,
		}

		self.proxy_holder.backend_api.network_create(self.testnetwork_network,self.testnetwork_attrs)
		self.proxy_holder.backend_api.network_create(self.testnetwork2_network,self.testnetwork2_attrs)

		self.testnetwork_id = self.proxy_holder.backend_core.network_list()[0]['id']
		self.testnetwork2_id = self.proxy_holder.backend_core.network_list()[1]['id']

		#Create network instances
		self.testnetwork_instance_network = self.testnetwork_network
		self.testnetwork_instance_host = self.get_host_name(self.test_host_addresses[0])
		self.testnetwork_instance_host2 = self.get_host_name(self.test_host_addresses[1])
		self.testnetwork_instance_attrs = {'bridge': 'vmbr0'}

		self.proxy_holder.backend_api.network_instance_create(self.testnetwork_instance_network, self.testnetwork_instance_host, self.testnetwork_instance_attrs)
		self.proxy_holder.backend_api.network_instance_create(self.testnetwork_instance_network, self.testnetwork_instance_host2, self.testnetwork_instance_attrs)

		self.testnetwork_instance_host1_id = self.proxy_holder.backend_api.network_instance_list()[0]['id']

		self.testnetwork2_instance_network = self.testnetwork_network
		self.testnetwork2_instance_host = self.get_host_name(self.test_host_addresses[1])
		self.testnetwork2_instance_attrs = {'bridge': 'vmbr0'}

		self.proxy_holder.backend_api.network_instance_create(self.testnetwork2_instance_network, self.testnetwork2_instance_host, self.testnetwork2_instance_attrs)


	@classmethod
	def tearDownClass(cls):
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()
		cls.remove_all_other_sites()


	def tearDown(self):
		self.remove_all_network_instances()
		self.remove_all_networks()




	#Get a list of all network_instances and check for correctness
	def test_network_instance_list(self):

		network_instance_list_api = self.proxy_holder.backend_api.network_instance_list()
		self.assertIsNotNone(network_instance_list_api)
		network_instance_list_core = self.proxy_holder.backend_core.network_instance_list()
		self.assertIsNotNone(network_instance_list_core)
		self.assertEqual(network_instance_list_api, network_instance_list_core)

	#Get a list of all network instances of kind *testnetwork2* and check for correctness
	def test_network_instance_list_with_network(self):

		network_instance_list_api = self.proxy_holder.backend_api.network_instance_list(network=self.testnetwork2_id)
		self.assertIsNotNone(network_instance_list_api)
		network_instance_list_core = self.proxy_holder.backend_core.network_instance_list(network=self.testnetwork2_id)
		self.assertIsNotNone(network_instance_list_core)
		self.assertEqual(network_instance_list_api, network_instance_list_core)

		for network in network_instance_list_api:
			self.assertEqual(network['network'], self.testnetwork2_network)

	#Get a list of all network instances provided by host[0] and check for correctness
	def test_network_instance_list_with_host(self):

		network_instance_list_api = self.proxy_holder.backend_api.network_instance_list(host=self.get_host_name(self.test_host_addresses[0]))
		self.assertIsNotNone(network_instance_list_api)
		network_instance_list_core = self.proxy_holder.backend_core.network_instance_list(host=self.get_host_name(self.test_host_addresses[0]))
		self.assertIsNotNone(network_instance_list_core)
		self.assertEqual(network_instance_list_api, network_instance_list_core)

		for network in network_instance_list_api:
			self.assertEqual(network['host'], self.get_host_name(self.test_host_addresses[0]))

	#Get a list of all network instances provided by host[0] and kind testnetwork_network and check for correctness
	def test_network_instance_list_with_network_and_host(self):

		network_instance_list_api = self.proxy_holder.backend_api.network_instance_list(network=self.testnetwork_id, host=self.get_host_name(self.test_host_addresses[0]))
		self.assertIsNotNone(network_instance_list_api)
		network_instance_list_core = self.proxy_holder.backend_core.network_instance_list(network=self.testnetwork_id, host=self.get_host_name(self.test_host_addresses[0]))
		self.assertIsNotNone(network_instance_list_core)
		self.assertEqual(network_instance_list_api, network_instance_list_core)

		for network in network_instance_list_api:
			self.assertEqual(network['host'], self.get_host_name(self.test_host_addresses[0]))
			self.assertEqual(network['network'], self.testnetwork_network)

	#Get a list of all network instances of non existing networks
	def test_network_instance_list_with_non_existing_network(self):

		network_id = self.testnetwork_id + self.testnetwork_id
		self.assertRaisesError(UserError,  UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_list, network=network_id)
		self.assertRaisesError(UserError,  UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.network_instance_list, network=network_id)

	#Create a correct network instance
	def test_network_instance_create(self):

		self.remove_all_network_instances()

		network_instance_api = self.proxy_holder.backend_api.network_instance_create(self.testnetwork_network,self.testnetwork_instance_host, self.testnetwork_instance_attrs)
		self.assertDictContainsSubset(self.testnetwork_instance_attrs, network_instance_api)
		self.assertIsNotNone(self.proxy_holder.backend_core.network_instance_list())

	#Create a correct network without permission
	def test_network_instance_create_without_permission(self):

		self.remove_all_network_instances()

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.network_instance_create, self.testnetwork_network, self.testnetwork_instance_host, self.testnetwork_instance_attrs)
		self.assertEqual(self.proxy_holder.backend_core.network_instance_list(), [])

	#Create a network instance for a non existing network
	def test_network_instance_create_non_existing_network(self):
		self.remove_all_network_instances()

		network = self.testnetwork_network+self.testnetwork_network
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_create, network, self.testnetwork_instance_host, self.testnetwork_instance_attrs)
		self.assertEqual(self.proxy_holder.backend_core.network_instance_list(), [])

	#Create a network instance for a non existing network
	def test_network_instance_create_non_existing_host(self):
		self.remove_all_network_instances()

		host = self.testnetwork_instance_host+self.testnetwork_instance_host
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_create, self.testnetwork_network, host, self.testnetwork_instance_attrs)
		self.assertEqual(self.proxy_holder.backend_core.network_instance_list(), [])

	#Modify existing network instance
	def test_network_instance_modify(self):

		network_attrs = self.testnetwork_instance_attrs.copy()
		network_attrs['bridge'] = "eth0"

		network_api = self.proxy_holder.backend_api.network_instance_modify(self.testnetwork_instance_host1_id, network_attrs)
		self.assertDictContainsSubset(network_attrs, network_api)

		network_core = self.proxy_holder.backend_core.network_instance_info(self.testnetwork_instance_host1_id)
		self.assertDictContainsSubset(network_attrs, network_core)

	#Modify existing network instance without permission
	def test_network_instance_modify_without_permission(self):

		network_attrs = self.testnetwork_instance_attrs.copy()
		network_attrs['bridge'] = "eth0"

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.network_instance_modify, self.testnetwork_instance_host1_id, network_attrs)

		network_core = self.proxy_holder.backend_core.network_instance_info(self.testnetwork_instance_host1_id)
		self.assertDictContainsSubset(self.testnetwork_instance_attrs, network_core)

	#Try to modify non existing network
	def test_network_instance_modify_non_existing_instance(self):
		network_attrs = self.testnetwork_instance_attrs.copy()
		network_attrs['bridger'] = "eth0"

		network_instance_id = self.testnetwork_instance_host1_id+self.testnetwork_instance_host1_id

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_modify, network_instance_id, network_attrs)


	#Modify existing network instance with incorrect parameters
	def test_network_instance_modify_with_incorrect_parameter(self):

		network_attrs = self.testnetwork_instance_attrs.copy()
		network_attrs['bridger'] = "eth0"

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.network_instance_modify, self.testnetwork_instance_host1_id, network_attrs)

		network_core = self.proxy_holder.backend_core.network_instance_info(self.testnetwork_instance_host1_id)
		self.assertDictContainsSubset(self.testnetwork_instance_attrs, network_core)

	#Modify host to non existing one
	def test_network_instance_modify_to_non_existing_host_parameter(self):

		network_attrs = self.testnetwork_instance_attrs.copy()
		network_attrs['host'] = self.testnetwork_instance_host+self.testnetwork_instance_host

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_modify, self.testnetwork_instance_host1_id, network_attrs)

		network_core = self.proxy_holder.backend_core.network_instance_info(self.testnetwork_instance_host1_id)
		self.assertDictContainsSubset(self.testnetwork_instance_attrs, network_core)

	#Modify network to non existing one
	def test_network_instance_modify_to_non_existing_network_parameter(self):

		network_attrs = self.testnetwork_instance_attrs.copy()
		network_attrs['network'] = self.testnetwork_instance_network+self.testnetwork_instance_network

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_modify, self.testnetwork_instance_host1_id, network_attrs)

		network_core = self.proxy_holder.backend_core.network_instance_info(self.testnetwork_instance_host1_id)
		self.assertDictContainsSubset(self.testnetwork_instance_attrs, network_core)

	#Remove network instance
	def test_network_instance_remove(self):

		self.proxy_holder.backend_api.network_instance_remove(self.testnetwork_instance_host1_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.network_instance_info, self.testnetwork_instance_host1_id)


	#Try to remove network instance without permission
	def test_network_instance_remove_without_permission(self):

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.network_instance_remove, self.testnetwork_instance_host1_id)
		self.assertIsNotNone(self.proxy_holder.backend_core.network_instance_info(self.testnetwork_instance_host1_id))

	#Try to remove non existing network instance
	def test_network_instance_remove_non_existing(self):

		network_instance_id = self.testnetwork_instance_host1_id+self.testnetwork_instance_host1_id
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_remove, network_instance_id)

	#Check if network instance info is unmodifed by the api
	def test_network_instance_info(self):

		network_instance_api = self.proxy_holder.backend_api.network_instance_info(self.testnetwork_instance_host1_id)
		network_instance_core = self.proxy_holder.backend_core.network_instance_info(self.testnetwork_instance_host1_id)

		self.assertIsNotNone(network_instance_api)
		self.assertIsNotNone(network_instance_core)
		self.assertEqual(network_instance_api, network_instance_core)

	#Check information of non existing network
	def test_network_instance_info_non_existing_network(self):

		network_instance_id = self.testnetwork_instance_host1_id+self.testnetwork_instance_host1_id
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.network_instance_info, network_instance_id)



def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(NetworkTestCase),
		unittest.TestLoader().loadTestsFromTestCase(NetworkInstanceTestCase),
	])