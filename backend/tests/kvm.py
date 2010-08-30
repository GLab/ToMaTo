'''
Created on Aug 30, 2010

@author: lemming
'''
import unittest
import tests
import glabnetman as api

TOP1 = '''
<topology name="test1">
	<device id="kvm1" type="kvm">
		<interface id="eth0"/>
		<interface id="eth1"/>
	</device>
</topology>
'''

TOP2 = '''
<topology name="test1">
	<device id="kvm1" type="kvm">
		<interface id="eth0"/>
	</device>
</topology>
'''

class Test(unittest.TestCase):

	def setUp(self):
		admin = api.login("admin", "123")
		api.host_add("host1a", "group1", "vmbr0", user=admin)
		api.host_add("host1b", "group1", "vmbr0", user=admin)
		api.host_add("host2a", "group2", "vmbr0", user=admin)
		api.host_add("host2b", "group2", "vmbr0", user=admin)
		api.template_add("tpl_openvz_1", "openvz", user=admin)
		api.template_add("tpl_openvz_2", "openvz", user=admin)
		api.template_set_default("openvz", "tpl_openvz_1", user=admin)
		api.template_add("tpl_kvm_1", "kvm", user=admin)
		api.template_add("tpl_kvm_2", "kvm", user=admin)
		api.template_set_default("kvm", "tpl_kvm_1", user=admin)
		tests.wait_for_tasks(api, admin)
		
 	def tearDown(self):
		admin = api.login("admin", "123")
		tests.wait_for_tasks(api, admin)		
		for top in api.top_list("*", "*", user=admin):
			api.top_remove(top["id"], user=admin)
		for host in api.host_list("*", user=admin):
			api.host_remove(host["name"], user=admin)
		for template in api.template_list("*", user=admin):
			api.template_remove(template["name"], user=admin)

	def testLifecycle(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		api.device_prepare(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_start(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_stop(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_destroy(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)

	def testChange(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		api.top_change(id, TOP2, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP1, user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_prepare(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP2, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP1, user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_start(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP2, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP1, user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_stop(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_destroy(id, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
