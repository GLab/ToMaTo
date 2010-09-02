'''
Created on Aug 30, 2010

@author: lemming
'''
import unittest
import tests
import glabnetman as api

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
		api.host_add("host1a", "group1", "vmbr0", user=admin)
		api.host_add("host1b", "group1", "vmbr0", user=admin)
		api.host_add("host2a", "group2", "vmbr0", user=admin)
		api.host_add("host2b", "group2", "vmbr0", user=admin)
		api.host_add("host2c", "group2", "vmbr0", user=admin)
		tests.wait_for_tasks(api, admin)
		assert len(api.host_list("*", user=admin)) == 5
		assert len(api.host_list("group1", user=admin)) == 2 
		assert len(api.host_list("group2", user=admin)) == 3
		api.host_remove("host2c", user=admin)
		assert len(api.host_list("group2", user=admin)) == 2

	