# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import unittest
import tomato as api

class Test(unittest.TestCase):

	def setUp(self):
		admin = api.login("admin", "123")
		for template in api.template_list("", user=admin):
			api.template_remove(template["name"], user=admin)

	def tearDown(self):
		admin = api.login("admin", "123")
		for template in api.template_list("", user=admin):
			api.template_remove(template["name"], user=admin)

	def testTemplates(self):
		admin = api.login("admin", "123")
		assert api.template_list("", user=admin) == []
		api.template_add("tpl_1", "openvz", "url1", user=admin)
		api.template_add("tpl_2", "kvm", "url2", user=admin)
		assert len(api.template_list("", user=admin)) == 2
		api.template_remove("tpl_1", user=admin)
		assert len(api.template_list("kvm", user=admin)) == 1

	def testTemplateDefaults(self):
		admin = api.login("admin", "123")
		api.template_add("tpl_1", "openvz", "url1", user=admin)
		api.template_add("tpl_2", "openvz", "url2", user=admin)
		api.template_add("tpl_3", "kvm", "url3", user=admin)
		api.template_add("tpl_4", "kvm", "url4", user=admin)
		api.template_set_default("kvm", "tpl_3", user=admin)
		api.template_set_default("openvz", "tpl_1", user=admin)
		
