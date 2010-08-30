'''
Created on Aug 30, 2010

@author: lemming
'''
import unittest
import tests
import glabnetman as api

class Test(unittest.TestCase):

	def setUp(self):
		admin = api.login("admin", "123")
		for template in api.template_list("*", user=admin):
			api.template_remove(template["name"], user=admin)

	def tearDown(self):
		admin = api.login("admin", "123")
		for template in api.template_list("*", user=admin):
			api.template_remove(template["name"], user=admin)

	def testTemplates(self):
		admin = api.login("admin", "123")
		assert api.template_list("*", user=admin) == []
		api.template_add("tpl_1", "openvz", user=admin)
		api.template_add("tpl_2", "kvm", user=admin)
		assert len(api.template_list("*", user=admin)) == 2
		api.template_remove("tpl_1", user=admin)
		assert len(api.template_list("kvm", user=admin)) == 1

	def testTemplateDefaults(self):
		admin = api.login("admin", "123")
		api.template_add("tpl_1", "openvz", user=admin)
		api.template_add("tpl_2", "openvz", user=admin)
		api.template_add("tpl_3", "kvm", user=admin)
		api.template_add("tpl_4", "kvm", user=admin)
		api.template_set_default("kvm", "tpl_3", user=admin)
		api.template_set_default("openvz", "tpl_1", user=admin)
		
