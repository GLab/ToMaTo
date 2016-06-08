from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import time


'''
## templates
### template_list
- Scenario 1: No parameters
- Scenario 2: Correct parameter
- Scenario 3: Non existing technology

### template_create
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters, without permission
- Scenario 3: Non existing technology
- Scenario 4: Already used name
- Scenario 5: Incorrect attributes

### template_modify
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters, without permission
- Scenario 3: Non existing template
- Scenario 4: Incorrect attributes

### template_remove
- Scenario 1: Correct parameter
- Scenario 2: Correct parameter, without permission
- Scenario 3: Non existing template

### template_info
- Scenario 1: Correct parameters
- Scenario 2: Correct parameters and including torrent data
- Scenario 3: Non existing template
'''


class TemplateTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()

		#Create user without permission to create profiles
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

		#Create template
		self.testtemplate_attrs = self.test_temps[0].copy()
		self.testtemplate_technology =  self.testtemplate_attrs['tech']
		self.testtemplate_name = self.testtemplate_attrs['name']
		del self.testtemplate_attrs['name']
		del self.testtemplate_attrs['tech']
		
		#second test_template
		self.testtemplate2 = self.test_temps[1].copy()

		self.proxy_holder.backend_core.template_create(self.testtemplate_technology, self.testtemplate_name, self.testtemplate_attrs)

		self.testtemplate_id = self.proxy_holder.backend_core.template_id(tech=self.testtemplate_technology, name=self.testtemplate_name)


	def tearDown(self):
		self.remove_all_templates()

	@classmethod
	def tearDownClass(cls):
		cls.remove_all_profiles()
		cls.remove_all_other_accounts()


	#Get template_list and check for correctness
	def test_template_list(self):

		template_list_api = self.proxy_holder.backend_api.template_list()
		self.assertIsNotNone(template_list_api)
		template_list_core = self.proxy_holder.backend_core.template_list()
		self.assertIsNotNone(template_list_core)
		self.assertEqual(template_list_api, template_list_core)


	#Get template list for specific technology  and check for correctness
	def test_template_list_with_parameter(self):

		template_list_api = self.proxy_holder.backend_api.template_list(self.testtemplate_technology)
		self.assertIsNotNone(template_list_api)
		template_list_core = self.proxy_holder.backend_core.template_list(self.testtemplate_technology)
		self.assertIsNotNone(template_list_core)
		self.assertEqual(template_list_api, template_list_core)

	#Get template list for non existing technology and check for emptiness
	def test_template_list_non_existing_technology(self):

		non_existing_technology = "closedvz"

		template_list_api = self.proxy_holder.backend_api.template_list(non_existing_technology)
		self.assertIsNotNone(template_list_api)
		template_list_core = self.proxy_holder.backend_core.template_list(non_existing_technology)
		self.assertIsNotNone(template_list_core)

	#Create a template with correct parameters
	def test_template_create(self):

		template_attrs = self.testtemplate2.copy()
		del template_attrs['tech']
		del template_attrs['name']

		template_api = self.proxy_holder.backend_api.template_create(self.testtemplate2['tech'], self.testtemplate2['name'], template_attrs)
		self.assertIsNotNone(template_api)
		template_id = self.proxy_holder.backend_core.template_id(self.testtemplate2['tech'], self.testtemplate2['name'])
		template_core = self.proxy_holder.backend_core.template_info(template_id)
		self.assertEqual(template_api, template_core)
		self.assertDictContainsSubset(template_attrs, template_api)

	#Create a template without permission
	def test_template_create_without_permission(self):

		template_attrs = self.testtemplate2.copy()
		del template_attrs['tech']
		del template_attrs['name']

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.template_create, self.testtemplate2['tech'], self.testtemplate2['name'], template_attrs)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.template_id, self.testtemplate2['tech'], self.testtemplate2['name'])

	#Create a template with an non existing technology

	def test_template_create_non_exsting_technology(self):

		template_technology = "closedvz"
		template_attrs = self.testtemplate2.copy()
		del template_attrs['tech']
		del template_attrs['name']

		self.assertRaisesError(UserError, UserError.INVALID_VALUE, self.proxy_holder.backend_api.template_create, template_technology, self.testtemplate2['name'], template_attrs)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.template_id, template_technology, self.testtemplate2['name'])

	#Create a duplicate and check for correct error
	def test_template_create_name_already_used(self):

		self.assertRaisesError(UserError, UserError.ALREADY_EXISTS, self.proxy_holder.backend_api.template_create,self.testtemplate_technology,self.testtemplate_name, self.testtemplate_attrs)

	#Try to create a invalid template
	def test_template_create_incorrect_attributes(self):

		template_attrs = self.testtemplate2.copy()
		template_attrs['asdha1'] = "attribute not existing"
		del template_attrs['tech']
		del template_attrs['name']

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.template_create, self.testtemplate2['tech'], self.testtemplate2['name'], template_attrs)

	#Modify a template and check for the correct changes
	def test_template_modify(self):

		template_attrs = self.testtemplate_attrs.copy()
		template_attrs['label'] = "Modifed " + template_attrs['label']

		template_api = self.proxy_holder.backend_api.template_modify(self.testtemplate_id, template_attrs)
		self.assertIsNotNone(template_api)
		template_core = self.proxy_holder.backend_core.template_info(self.testtemplate_id)
		self.assertEqual(template_api, template_core)

	#Modify a template without permission
	def test_template_modify_without_permission(self):

		template_attrs = self.testtemplate_attrs.copy()
		template_attrs['label'] = "Modifed " + template_attrs['label']

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.template_modify, self.testtemplate_id, template_attrs)


	#Modify a non existing template
	def test_template_modify_non_existing_template(self):

		template_attrs = self.testtemplate_attrs.copy()
		template_attrs['label'] = "Modifed " + template_attrs['label']

		self.proxy_holder.backend_api.template_remove(self.testtemplate_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.template_modify, self.testtemplate_id, template_attrs)


	#Modify a template and add incorrect parameters
	def test_template_modify_with_incorrect_parameters(self):

		template_attrs = self.testtemplate_attrs.copy()
		template_attrs['weight'] =  50
		template_attrs['label'] = "Modifed " + template_attrs['label']

		self.assertRaisesError(UserError, UserError.UNSUPPORTED_ATTRIBUTE, self.proxy_holder.backend_api.template_modify, self.testtemplate_id, template_attrs)

	#Remove a template
	def test_template_remove(self):

		self.proxy_holder.backend_api.template_remove(self.testtemplate_id)
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_core.template_info, self.testtemplate_id)

	#Remove a template without permission
	def test_template_remove_without_permission(self):

		self.assertRaisesError(UserError, UserError.DENIED, self.proxy_holder_tester.backend_api.template_remove, self.testtemplate_id)
		info_core = self.proxy_holder.backend_core.template_info(self.testtemplate_id)
		self.assertIsNotNone(info_core)

	#Remove a non existing template
	def test_template_remove_non_existing(self):

		#Non existing ID
		test_id = self.testtemplate_id + self.testtemplate_id
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.template_remove, test_id)

	#get template informations and check for correctness
	def test_template_info(self):

		test_info_api = self.proxy_holder.backend_api.template_info(self.testtemplate_id)

		self.assertIsNotNone(test_info_api)
		test_info_core = self.proxy_holder.backend_core.template_info(self.testtemplate_id)
		self.assertIsNotNone(test_info_core)
		self.assertEqual(test_info_api, test_info_core)
		self.assertDictContainsSubset(self.testtemplate_attrs, test_info_api)

	#Get template informations and  and check for correctness
	def test_template_info_with_torrent_data(self):

		test_info_api = self.proxy_holder.backend_api.template_info(self.testtemplate_id, True)

		self.assertIsNotNone(test_info_api)
		self.assertDictContainsSubset(self.testtemplate_attrs, test_info_api)
		test_info_core = self.proxy_holder.backend_core.template_info(self.testtemplate_id, True)
		self.assertDictContainsSubset(self.testtemplate_attrs, test_info_core)
		self.assertIsNotNone(test_info_core)
		self.assertEqual(test_info_api, test_info_core)

	#Get template informations of a non existing template
	def test_template_info_non_existing(self):
		template_id = self.testtemplate_id + self.testtemplate_id
		self.assertRaisesError(UserError, UserError.ENTITY_DOES_NOT_EXIST, self.proxy_holder.backend_api.template_info, template_id)


def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(TemplateTestCase),
	])
