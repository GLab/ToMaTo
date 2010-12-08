'''
Created on Aug 30, 2010

@author: lemming
'''
import unittest
import tests
import tomato as api

TOP1 = '''
<topology name="test1">
	<device name="openvz1" type="openvz" root_password="test123">
		<interface name="eth0" use_dhcp="true"/>
		<interface name="eth1" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
	</device>
</topology>
'''

TOP2 = '''
<topology name="test1">
	<device name="openvz1" type="openvz" root_password="test1234">
		<interface name="eth0" use_dhcp="true"/>
		<interface name="eth1" ip4address="10.1.2.1/24" gateway="10.1.2.254"/>
		<interface name="eth2" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
	</device>
</topology>
'''

class Test(unittest.TestCase):

	def setUp(self):
		tests.default_setUp()
		
	def tearDown(self):
		tests.default_tearDown()

	def testLifecycle(self):
		admin = api.login("admin", "123")
		tid = api.top_import(TOP1, user=admin)
		api.device_prepare(tid, "openvz1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_start(tid, "openvz1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_stop(tid, "openvz1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.device_destroy(tid, "openvz1", user=admin)
		tests.wait_for_tasks(api, admin)

	def testChange(self):
		admin = api.login("admin", "123")
		tid = api.top_import(TOP1, user=admin)
		api.top_modify(tid, tests.encode_modification("device-rename", "openvz1", None, {"name": "openvz2"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("device-configure", "openvz2", None, {"hostgroup": "test"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("device-delete", "openvz2", None, {}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("device-create", None, None, {"type": "openvz", "name": "openvz1"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("interface-create", "openvz1", None, {"name": "eth0"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("interface-configure", "openvz1", "eth0", {}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("interface-rename", "openvz1", "eth0", {"name": "eth1"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("interface-delete", "openvz1", "eth1", {}), user=admin)
		tests.wait_for_tasks(api, admin)
