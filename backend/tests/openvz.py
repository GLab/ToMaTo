'''
Created on Aug 30, 2010

@author: lemming
'''
import unittest
import tests
import tomato as api

TOP1 = [
	tests.encode_mod("topology-rename", None, None, {"name": "test1"}),
	tests.encode_mod("device-create", None, None, {"name": "openvz1", "type": "openvz"}),
	tests.encode_mod("device-configure", "openvz1", None, {"root_password": "test123", "gateway": "10.1.1.254"}),
	tests.encode_mod("interface-create", "openvz1", None, {"name": "eth0"}),
	tests.encode_mod("interface-configure", "openvz1", "eth0", {"use_dhcp": "true"}),
	tests.encode_mod("interface-create", "openvz1", None, {"name": "eth1"}),
	tests.encode_mod("interface-configure", "openvz1", "eth1", {"ip4address": "10.1.1.1/24"}),
]

TOP2 = [
	tests.encode_mod("topology-rename", None, None, {"name": "test2"}),
	tests.encode_mod("device-create", None, None, {"name": "openvz1", "type": "openvz"}),
	tests.encode_mod("device-configure", "openvz1", None, {"root_password": "test1234", "gateway": "10.1.1.254"}),
	tests.encode_mod("interface-create", "openvz1", None, {"name": "eth0"}),
	tests.encode_mod("interface-configure", "openvz1", "eth0", {"use_dhcp": "true"}),
	tests.encode_mod("interface-create", "openvz1", None, {"name": "eth1"}),
	tests.encode_mod("interface-configure", "openvz1", "eth1", {"ip4address": "10.1.1.1/24"}),
	tests.encode_mod("interface-create", "openvz1", None, {"name": "eth2"}),
	tests.encode_mod("interface-configure", "openvz1", "eth2", {"ip4address": "10.1.2.1/24"}),
]

class Test(unittest.TestCase):

	def setUp(self):
		tests.default_setUp()
		
	def tearDown(self):
		tests.default_tearDown()

	def testLifecycle(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, True, user=admin)
		api.top_action(tid, "device", "openvz1", "prepare", direct=True, user=admin)
		api.top_action(tid, "device", "openvz1", "start", direct=True, user=admin)
		api.top_action(tid, "device", "openvz1", "stop", direct=True, user=admin)
		api.top_action(tid, "device", "openvz1", "destroy", direct=True, user=admin)

	def testChange(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP2, True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-rename", "openvz1", None, {"name": "openvz2"})], True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-configure", "openvz2", None, {"hostgroup": "test"})], True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-delete", "openvz2", None, {})], True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-create", None, None, {"type": "openvz", "name": "openvz1"})], True, user=admin)
		api.top_modify(tid, [tests.encode_mod("interface-create", "openvz1", None, {"name": "eth0"})], True, user=admin)
		api.top_modify(tid, [tests.encode_mod("interface-configure", "openvz1", "eth0", {})], True, user=admin)
		api.top_modify(tid, [tests.encode_mod("interface-rename", "openvz1", "eth0", {"name": "eth1"})], True, user=admin)
		api.top_modify(tid, [tests.encode_mod("interface-delete", "openvz1", "eth1", {})], True, user=admin)
