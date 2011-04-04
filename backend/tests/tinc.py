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

TOP1 = [
	tests.encode_mod("topology-rename", None, None, {"name": "test1"}),
	tests.encode_mod("device-create", None, None, {"name": "openvz1", "type": "openvz"}),
	tests.encode_mod("device-configure", "openvz1", None, {"root_password": "test123", "gateway": "10.1.1.254"}),
	tests.encode_mod("interface-create", "openvz1", None, {"name": "eth0"}),
	tests.encode_mod("interface-configure", "openvz1", "eth0", {"use_dhcp": "true"}),
	tests.encode_mod("interface-create", "openvz1", None, {"name": "eth1"}),
	tests.encode_mod("interface-configure", "openvz1", "eth1", {"ip4address": "10.1.1.1/24"}),
	tests.encode_mod("device-create", None, None, {"name": "kvm1", "type": "kvm"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth0"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth1"}),
	tests.encode_mod("connector-create", None, None, {"name": "switch1", "type": "switch"}),
	tests.encode_mod("connection-create", "switch1", None, {"interface": "openvz1.eth0"}),
	tests.encode_mod("connection-create", "switch1", None, {"interface": "kvm1.eth0"}),
	tests.encode_mod("connector-create", None, None, {"name": "router1", "type": "router"}),
	tests.encode_mod("connection-create", "router1", None, {"interface": "openvz1.eth1", "gateway": "10.1.1.254/24"}),
	tests.encode_mod("connection-create", "router1", None, {"interface": "kvm1.eth1", "gateway": "10.1.2.254/24"}),
]

class Test(unittest.TestCase):

	def setUp(self):
		tests.default_setUp()
		
	def tearDown(self):
		tests.default_tearDown()

	def testLifecycle(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, direct=True, user=admin)
		api.top_action(tid, "device", "openvz1", "prepare", direct=True, user=admin)
		api.top_action(tid, "device", "kvm1", "prepare", direct=True, user=admin)
		api.top_action(tid, "connector", "switch1", "prepare", direct=True, user=admin)
		api.top_action(tid, "connector", "switch1", "start", direct=True, user=admin)
		api.top_action(tid, "connector", "switch1", "stop", direct=True, user=admin)
		api.top_action(tid, "connector", "switch1", "destroy", direct=True, user=admin)
		api.top_action(tid, "connector", "router1", "prepare", direct=True, user=admin)
		api.top_action(tid, "connector", "router1", "start", direct=True, user=admin)
		api.top_action(tid, "connector", "router1", "stop", direct=True, user=admin)
		api.top_action(tid, "connector", "router1", "destroy", direct=True, user=admin)

	def testChange(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connector-rename", "switch1", None, {"name": "switch2"})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connector-configure", "router1", None, {})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connection-delete", "router1", "openvz1.eth1", {})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connection-delete", "router1", "kvm1.eth1", {})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connector-delete", "router1", None, {})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connector-create", None, None, {"type": "switch", "name": "switch1"})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connection-create", "switch1", None, {"interface": "openvz1.eth1"})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("connection-create", "switch1", None, {"interface": "kvm1.eth1"})], direct=True, user=admin)
