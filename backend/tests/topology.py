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
	tests.encode_mod("device-create", None, None, {"name": "ovz1", "type": "openvz", "root_password": "test", "gateway": "10.1.1.254/24"}),
	tests.encode_mod("interface-create", "ovz1", None, {"name": "eth0", "use_dhcp": "true"}),
	tests.encode_mod("interface-create", "ovz1", None, {"name": "eth1", "ip4address": "10.1.1.1/24"}),
	tests.encode_mod("interface-create", "ovz1", None, {"name": "eth2", "use_dhcp": "true"}),
	tests.encode_mod("interface-create", "ovz1", None, {"name": "eth3", "use_dhcp": "true"}),
	tests.encode_mod("device-create", None, None, {"name": "kvm1", "type": "kvm"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth0"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth1"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth2"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth3"}),
	tests.encode_mod("connector-create", None, None, {"name": "internet", "type": "external", "network_type": "internet"}),
	tests.encode_mod("connection-create", "internet", None, {"interface": "ovz1.eth0"}),
	tests.encode_mod("connection-create", "internet", None, {"interface": "kvm1.eth0"}),
	tests.encode_mod("connector-create", None, None, {"name": "hub1", "type": "hub"}),
	tests.encode_mod("connection-create", "hub1", None, {"interface": "ovz1.eth1", "lossratio": "0.1", "delay": "50", "bandwidth": "200"}),
	tests.encode_mod("connection-create", "hub1", None, {"interface": "kvm1.eth1"}),
	tests.encode_mod("connector-create", None, None, {"name": "switch1", "type": "switch"}),
	tests.encode_mod("connection-create", "switch1", None, {"interface": "ovz1.eth2", "lossratio": "0.1", "delay": "50", "bandwidth": "200"}),
	tests.encode_mod("connection-create", "switch1", None, {"interface": "kvm1.eth2"}),
	tests.encode_mod("connector-create", None, None, {"name": "router1", "type": "router"}),
	tests.encode_mod("connection-create", "router1", None, {"interface": "ovz1.eth3", "lossratio": "0.1", "delay": "50", "bandwidth": "200", "gateway": "10.1.1.254/24"}),
	tests.encode_mod("connection-create", "router1", None, {"interface": "kvm1.eth3", "gateway": "10.1.2.254/24"}),	
]

class Test(unittest.TestCase):

	def setUp(self):
		tests.default_setUp()
		
	def tearDown(self):
		tests.default_tearDown()

	def testImport(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, direct=True, user=admin)
		assert tid
		tlist = api.top_list("", "", "", user=admin)
		assert len(tlist) == 1
		assert tlist[0]["attrs"]["name"] == "test1"

	def testExport(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, direct=True, user=admin)
		assert len(api.top_info(tid, user=admin)["devices"]) > 1

	def testInfo(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, direct=True, user=admin)
		info = api.top_info(tid, user=admin)
		assert info["id"] == tid
		assert info["attrs"]["name"] == "test1"
		assert info["attrs"]["owner"] == "admin"
		assert info["attrs"]["device_count"] == 2
		assert info["attrs"]["connector_count"] == 4

	def testLifecycle(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, direct=True, user=admin)
		api.top_action(tid, "topology", None, "prepare", direct=True, user=admin)
		api.top_action(tid, "topology", None, "start", direct=True, user=admin)
		api.top_action(tid, "topology", None, "stop", direct=True, user=admin)
		api.top_action(tid, "topology", None, "destroy", direct=True, user=admin)
		api.top_action(tid, "topology", None, "start", direct=True, user=admin)
		api.top_action(tid, "topology", None, "destroy", direct=True, user=admin)
		api.top_action(tid, "topology", None, "remove", direct=True, user=admin)