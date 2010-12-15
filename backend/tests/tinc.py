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

TOP1 = '''
<topology name="test1">
	<device name="openvz1" type="openvz" root_password="test123">
		<interface name="eth0" use_dhcp="true"/>
		<interface name="eth1" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
		<interface name="eth2" use_dhcp="true"/>
	</device>
	<device name="kvm1" type="kvm">
		<interface name="eth0"/>
		<interface name="eth1"/>
	</device>
	<connector name="switch1" type="switch">
		<connection interface="openvz1.eth0"/>
		<connection interface="kvm1.eth0"/>
	</connector> 
	<connector name="router1" type="router">
		<connection interface="openvz1.eth1" gateway="10.1.1.254/24"/>
		<connection interface="kvm1.eth1" gateway="10.1.2.254/24"/>
	</connector> 
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
		api.device_prepare(tid, "kvm1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_prepare(tid, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_start(tid, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_stop(tid, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_destroy(tid, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_prepare(tid, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_start(tid, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_stop(tid, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_destroy(tid, "router1", user=admin)
		tests.wait_for_tasks(api, admin)

	def testChange(self):
		admin = api.login("admin", "123")
		tid = api.top_import(TOP1, user=admin)
		api.top_modify(tid, tests.encode_modification("connector-rename", "switch1", None, {"name": "switch2"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("connector-configure", "router1", None, {}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("connection-delete", "router1", "openvz1.eth1", {}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("connection-delete", "router1", "kvm1.eth1", {}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("connector-delete", "router1", None, {}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("connector-create", None, None, {"type": "switch", "name": "switch1"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("connection-create", "switch1", None, {"interface": "openvz1.eth1"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(tid, tests.encode_modification("connection-create", "switch1", None, {"interface": "kvm1.eth1"}), user=admin)
		tests.wait_for_tasks(api, admin)		