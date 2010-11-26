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
import tests
import tomato as api

class Test(unittest.TestCase):

	def setUp(self):
		admin=api.login("admin","123")
		for host in api.host_list("*", admin):
			api.host_remove(host["name"], admin)

	def tearDown(self):
		admin=api.login("admin","123")
		tests.wait_for_tasks(api, admin)
		for host in api.host_list("*", admin):
			api.host_remove(host["name"], admin)

	def testHosts(self):
		admin=api.login("admin","123")
		assert api.host_list("*", user=admin) == []
		api.host_add("host1a", "group1", True, 0, 10, 0, 10, 0, 10, user=admin)
		api.host_add("host1b", "group1", True, 0, 10, 0, 10, 0, 10, user=admin)
		api.host_add("host2a", "group2", True, 0, 10, 0, 10, 0, 10, user=admin)
		api.host_add("host2b", "group2", True, 0, 10, 0, 10, 0, 10, user=admin)
		api.host_add("host2c", "group2", True, 0, 10, 0, 10, 0, 10, user=admin)
		tests.wait_for_tasks(api, admin)
		assert len(api.host_list("*", user=admin)) == 5
		assert len(api.host_list("group1", user=admin)) == 2 
		assert len(api.host_list("group2", user=admin)) == 3
		api.host_remove("host2c", user=admin)
		assert len(api.host_list("group2", user=admin)) == 2

	