from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import time
import unittest
"""
## elements
### element_create
-  Scenario 1: Correct parameters
-  Scenario 2: Correct parameters, without permission
-  Scenario 3: Create all existing technologies, start them and check for correctness.
-  Scenario 4: existing type in existing topology without parent and attributes
-  Scenario 5: not existing type and the other parameters correct
-  Scenario 6: correct parameters and incorrect attributes
-  Scenario 6.1: Non existing profile
-  Scenario 6.2: Non existing template
-  Scenario 7: existing type in non existing topology
-  Scenario 8: existing type and correct topology with non existing parent
-  Scenario 9: existing type and correct topology with existing parent, but parent is an interface
-  Scenario 10: existing type and correct topology with existing parent, but self is not an interface type
-  Scenario 11: existing type and correct topology with existing parent, but parent is in different topology

### element_modify
-  Scenario 1: Correct parameters
-  Scenario 2: Correct parameters, without permission
-  Scenario 3: Non existing element
-  Scenario 4: Non existing attribute
-  Scenario 5: Non existing template
-  Scenario 6: Non existing profile
-  Scenario 7: No permission for template
-  Scenario 8: No permission for profile

### element_remove
-  Scenario 1: Correct parameter
-  Scenario 2: Correct parameter, without permission
-  Scenario 3: Non existing element
-  Scenario 4: Remove element with child elements

### element_info
-  Scenario 1: Correct parameter
-  Scenario 2: Non existing element
-  Scenario 3: Correct id and fetch=True (and child element)

### element_usage
-  Scenario 1: Correct parameter
-  Scenario 2: Non existing element

### host_remove (one scenario that should be best placed here)
-  Scenario 3: remove host with started element
"""
class ElementTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()

		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)

		cls.add_templates_if_missing()

		for temp in cls.proxy_holder.backend_core.template_list():
			if temp['name'] == cls.test_temps[0]['name']:
				cls.test_temp1_id = temp['id']

		# Create test profiles
		cls.add_profiles()
		cls.restricted_profile_name = "%s_restricted" % cls.default_profile_name
		
		# Create user without permission to create profiles
		testuser_username = "testuser"
		testuser_password = "123"
		testuser_organization = cls.default_organization_name
		testuser_attrs = {"realname": "Test User",
						  "email": "test@example.com",
						  "flags": {'over_quota': True}
						  }

		cls.testuser = cls.proxy_holder.backend_api.account_create(testuser_username, testuser_password,
																	 testuser_organization,
																	 testuser_attrs)
		cls.proxy_holder_tester = ProxyHolder(testuser_username, testuser_password)

		# Give admin access to restricted profiles and templates
		flags = {}
		flags["restricted_profiles"] = True
		flags["restricted_templates"] = True
		cls.proxy_holder.backend_api.account_modify(cls.default_user_name, {'flags': flags})

		

		cls.testtopology = cls.proxy_holder.backend_core.topology_create(cls.default_user_name)
		cls.testtopology_id = cls.testtopology['id']




	def setUp(self):
	

		self.testelement_attrs = {
			"profile": self.default_profile_name,
			"name": "Ubuntu 12.04 (x86) #1",
			"template":  self.test_temps[0]['name']
			}

		self.testelement = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																		 type=self.test_temps[0]['type'],
																		 attrs=self.testelement_attrs)
		self.testelement_id = self.testelement['id']

		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "start")
		self.testelement = self.proxy_holder.backend_core.element_info(self.testelement_id)
		self.testelement_id = self.testelement['id']


	def tearDown(self):

		self.proxy_holder.backend_core.topology_set_permission(self.testtopology_id,self.testuser["name"], "null")
		self.remove_all_elements()


	@classmethod
	def tearDownClass(cls):
		cls.proxy_holder.backend_core.topology_action(cls.testtopology_id, "stop")
		cls.remove_all_connections()
		cls.remove_all_elements()
		cls.remove_all_topologies()
		cls.remove_all_templates()
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()
		cls.remove_all_hosts()

	#Just check if element info will be returned without modification
	def test_element_info(self):
		"""
		Check if informations are correct and not modified
		"""
		element_info_api = self.proxy_holder.backend_api.element_info(self.testelement_id)
		element_info_core = self.proxy_holder.backend_core.element_info(self.testelement_id)
		self.assertDictEqual(element_info_api, element_info_core)

	def test_element_info_without_permission(self):
		"""
		Check if permissions are checked for element info
		"""
		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.element_info, self.testelement_id)

	def test_element_info_non_existing(self):
		"""
		Check if API respondes correctly to non existing elements
		"""
		testelement_id = self.testelement_id[12:24] + self.testelement_id[0:12]

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_info, testelement_id)

	def test_element_info_with_fetch_true(self):
		"""
		Test if all informations of subelements are fetched into the info call
		"""
		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "stop")

		self.testelement1_interface = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																				  type=self.test_temps[0][
																						   'type'] + "_interface",
																				  parent=self.testelement_id)

		element_info_api = self.proxy_holder.backend_api.element_info(self.testelement_id,fetch=True)
		element_info_core = self.proxy_holder.backend_core.element_info(self.testelement_id,fetch=True)
		self.assertDictEqual(element_info_api, element_info_core)

	def test_element_remove(self):

		"""
		Remove an element
		"""
		self.proxy_holder.backend_core.element_action(self.testelement_id, "stop")
		self.proxy_holder.backend_core.element_action(self.testelement_id, "destroy")

		self.proxy_holder.backend_api.element_remove(self.testelement_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.element_info, self.testelement_id)

	def test_element_remove_without_permission(self):
		"""
		Try to remove an element without permission
		"""
		self.proxy_holder.backend_core.element_action(self.testelement_id, "stop")
		self.proxy_holder.backend_core.element_action(self.testelement_id, "destroy")
		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.element_remove,self.testelement_id)

	def test_element_remove_non_existing(self):
		"""
		Try to remove a non existing element and check for correct response
		"""
		element_id = self.testelement_id[12:24] + self.testelement_id[0:12]
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.element_remove, element_id)

	def test_element_remove_with_children(self):
		"""
		Create an child element for an element and try to remove the parent
		"""
		self.proxy_holder.backend_core.element_action(self.testelement_id, "stop")
		self.proxy_holder.backend_core.element_action(self.testelement_id, "destroy")

		testelement1_interface = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																					type=self.test_temps[0][
																							 'type'] + "_interface",
																					parent=self.testelement_id)

		self.proxy_holder.backend_api.element_remove(self.testelement_id)

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.element_info, self.testelement_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.element_info, testelement1_interface['id'])

	def test_element_create(self):
		"""
		Create an element with correct attributes
		"""
		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}

		self.testelement = self.proxy_holder.backend_api.element_create(top=self.testtopology_id,
																		 type=self.test_temps[0]['type'],
																		 attrs=testelement_attrs)
		self.assertIsNotNone(self.testelement)

	def test_element_create_with_non_existing_profile(self):
		"""
		Create an element with non existing profile and check for correct response
		"""
		profile = "%s%s"%(self.default_profile_name, self.default_profile_name)

		testelement_attrs = {
			"profile": profile,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_create,
																			top=self.testtopology_id,
																			type=self.test_temps[0]['type'],
																			attrs=testelement_attrs)

	def test_element_create_with_non_existing_template(self):
		"""
		Create an element with non existing template and check for correct response
		"""
		template = "%s%s" % (self.test_temps[0]['name'], self.test_temps[0]['name'])

		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": template
		}

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST,
							   self.proxy_holder.backend_api.element_create,
							   top=self.testtopology_id,
							   type=self.test_temps[0]['type'],
							   attrs=testelement_attrs)


	def test_element_create_without_parents_and_attrs(self):

		"""
		Create an element without parent and attrs attribute
		"""
		self.testelement = self.proxy_holder.backend_api.element_create(top=self.testtopology_id,
																		 type=self.test_temps[0]['type'])

		self.assertIsNotNone(self.testelement)

	def test_element_create_non_existing_type(self):
		"""
		Create an element with a non existing technology type and check for correct response
		"""
		type = "closedvz"

		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_create, top=self.testtopology_id,
																		 type=type,
																		 attrs=testelement_attrs)

	def test_element_create_non_existing_topology(self):
		"""
		Create an element in a non existing topology and check for correct response
		"""
		topology_id = self.testtopology_id[12:24]+self.testtopology_id[0:12]

		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_create,top=topology_id,
																		 type=self.test_temps[0]['type'],
																		 attrs=testelement_attrs)

	def test_element_create_non_existing_parent(self):
		"""
		Create an child element for a non existing parant and check for correct response
		"""
		parent_id = self.testelement_id[12:24] + self.testelement_id[0:12]

		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_create, top=self.testtopology_id,
																		 type=self.test_temps[0]['type'],
																		 parent=parent_id,
																		 attrs=testelement_attrs)

	def test_element_create_existing_parent_from_different_topology(self):
		"""
		Create an child element for an existing element but with the parent in a different topology
		"""
		topology = self.proxy_holder.backend_core.topology_create(self.default_user_name)
		topology_id = topology['id']

		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}

		self.assertRaisesError(UserError, UserError.INVALID_CONFIGURATION, self.proxy_holder.backend_api.element_create, top=topology_id,
																		 type=self.test_temps[0]['type'],
																		 parent=self.testelement_id,
																		 attrs=testelement_attrs)

	def test_element_create_existing_parent_is_an_interface(self):
		"""
		Create an child element for an interface and check for correct response
		"""
		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}


		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "stop")

		testelement_interface = self.proxy_holder.backend_core.element_create(top=self.testtopology_id,
																		type=self.test_temps[0]['type']+"_interface",
																		parent=self.testelement_id)
		testelement_interface_id = testelement_interface["id"]


		self.assertRaisesError(UserError, UserError.INVALID_VALUE, self.proxy_holder.backend_api.element_create, top=self.testtopology_id,
							   type=self.test_temps[0]['type'],
							   parent=testelement_interface_id,
							   attrs=testelement_attrs)

	def test_element_create_with_parent_but_element_is_not_an_interface(self):
		"""
		Create an not valid child element
		"""
		testelement_attrs = {
			"profile": self.default_profile_name,
			"name": self.test_temps[0]['label'],
			"template": self.test_temps[0]['name']
		}

		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "stop")

		self.assertRaisesError(UserError, UserError.INVALID_VALUE, self.proxy_holder.backend_api.element_create,
							   top=self.testtopology_id,
							   type=self.test_temps[0]['type'],
							   parent=self.testelement_id,
							   attrs=testelement_attrs)


	def test_element_create_for_all_technologies(self):
		"""
		Create an element for each template to test all technologies
		"""
		for temp in self.test_temps:
			self.testelement_attrs = {
				"profile": self.default_profile_name,
				"name": temp['label'],
				"template": temp['name']
			}

			self.testelement = self.proxy_holder.backend_api.element_create(top=self.testtopology_id,
																		 type=temp['type'],
																		 attrs=self.testelement_attrs)
			self.assertIsNotNone(self.testelement)

	def test_element_create_without_permission(self):
		"""
		Try to create an element without the permission and check for correct response
		"""
		self.testelement_attrs = {
				"profile": self.default_profile_name,
				"name": self.test_temps[0]['label'],
				"template": self.test_temps[0]['name']
			}

		self.assertRaisesError(UserError, UserError.DENIED,self.proxy_holder_tester.backend_api.element_create,top=self.testtopology_id,
																		 type=self.test_temps[0]['type'],
																		 attrs=self.testelement_attrs)


	def test_element_modify(self):
		"""
		Try to modify an element correctly
		"""
		testelement_attrs = {
			"name": "%s %s"%(self.testelement["name"], self.testelement["name"]),
		}

		testelement = self.proxy_holder.backend_api.element_modify(self.testelement_id,testelement_attrs)

		self.assertIsNotNone(self.testelement)
		self.assertEqual(testelement_attrs["name"],testelement["name"])

	def test_element_modify_without_permission(self):
		"""
		Try to modify an element without the permission and check for correct response
		"""
		testelement_attrs = {
			"name": "%s %s"%(self.testelement["name"], self.testelement["name"]),
		}

		self.assertRaisesError(UserError,UserError.DENIED, self.proxy_holder_tester.backend_api.element_modify,self.testelement_id, testelement_attrs)

	def test_element_modify_non_existing(self):
		"""
		Try to modify an non existing element and check for correct response
		"""
		testelement_attrs = {
			"name": "%s %s"%(self.testelement["name"], self.testelement["name"]),
		}

		element_id = self.testelement_id[12:24]+self.testelement_id[0:12]

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_modify,
							element_id, testelement_attrs)

	def test_element_modify_non_existing_attribute(self):
		"""
		try to modify an non existing attribute
		"""
		testelement_attrs = {
			"namee": "%s %s" % (self.testelement["name"],self.testelement["name"]),
		}

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.element_modify,
							self.testelement_id, testelement_attrs)


	def test_element_modify_non_existing_template(self):
		"""
		Try to modify the element and use a non existing template
		"""
		testelement_attrs = {
			"name": "%s %s" % (self.testelement["name"],self.testelement["name"]),
			"template": "%s %s" % (self.testelement["template"],self.testelement["template"])
		}

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST,	self.proxy_holder.backend_api.element_modify,
							self.testelement_id, testelement_attrs)

	def test_element_modify_non_existing_profile(self):
		"""
		Try to modify the element and use a non existing profile
		"""
		testelement_attrs = {
			"name": "%s %s" % (self.testelement["name"],self.testelement["name"]),
			"profile": "%s %s" % (self.testelement["profile"],self.testelement["profile"])
		}

		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST,	self.proxy_holder.backend_api.element_modify,
							self.testelement_id, testelement_attrs)

	def test_element_modify_no_permission_for_template(self):
		"""
		Try to modify the element and use a template for which the user has no permission
		"""
		self.proxy_holder.backend_core.topology_set_permission(self.testtopology_id,self.testuser["name"], "manager")
		temp_restricted = {}
		for temp in self.test_temps:
			if(temp["restricted"] == True and temp["type"] ==self.testelement["type"]):
				temp_restricted = temp

		testelement_attrs = {
			"name": "%s %s" % (self.testelement["name"],self.testelement["name"]),
			"template": temp_restricted["name"],
		}

		self.assertRaisesError(UserError, UserError.DENIED,	self.proxy_holder_tester.backend_api.element_modify,
							self.testelement_id, testelement_attrs)

	def test_element_modify_no_permission_for_profile(self):
		"""
		Try to modify the element and use a profile for which the user has no permission
		"""
		self.proxy_holder.backend_core.topology_set_permission(self.testtopology_id,self.testuser["name"], "manager")

		self.proxy_holder.backend_core.topology_action(self.testtopology_id, "destroy")

		testelement_attrs = {
			"name": "%s %s" % (self.testelement["name"],self.testelement["name"]),
			"profile": self.restricted_profile_name,
		}

		self.assertRaisesError(UserError, UserError.DENIED,self.proxy_holder_tester.backend_api.element_modify,
							self.testelement_id, testelement_attrs)


	def test_element_usage(self):
		"""
		Get usage data for an element
		"""

		hostelement_id = "%d@%s"%(self.testelement['debug']['host_elements'][0][1],self.testelement['debug']['host_elements'][0][0])

		self.proxy_holder.backend_accounting.push_usage(elements={hostelement_id: [(int(time.time()), 0.0, 0.0, 0.0, 0.0)]},connections={})
		element_info_api = self.proxy_holder.backend_api.element_usage(self.testelement_id)
		element_info_core = self.proxy_holder.backend_accounting.get_record("element", self.testelement_id)


		self.assertDictEqual(element_info_api, element_info_core)

	def test_element_usage_non_existing_element(self):
		"""
		Get usage data for an non existing element and check for correct response
		"""
		testelement_id = self.testelement_id[12:24] + self.testelement_id[0:12]
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.element_usage, testelement_id)

	def test_host_remove_with_existing_element(self):
		"""
		Try to remove a host which has running elements and check for correct response
		"""
		self.assertRaisesError(UserError, UserError.NOT_EMPTY, self.proxy_holder.backend_api.host_remove,self.testelement['debug']['host_elements'][0][0])

