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
	<device name="ovz1" type="openvz" root_password="test">
		<interface name="eth0" use_dhcp="true"/>
		<interface name="eth1" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
		<interface name="eth2" use_dhcp="true"/>
		<interface name="eth3" use_dhcp="true"/>
	</device>
	<device name="kvm1" type="kvm">
		<interface name="eth0"/>
		<interface name="eth1"/>
		<interface name="eth2"/>
		<interface name="eth3"/>
	</device>
	<connector name="internet" type="special" feature_type="internet">
		<connection interface="ovz1.eth0"/>
		<connection interface="kvm1.eth0"/>
	</connector>
	<connector name="hub1" type="hub">
		<connection interface="ovz1.eth1" lossratio="0.1" delay="50" bandwidth="200"/>
		<connection interface="kvm1.eth1"/>
	</connector>
	<connector name="switch1" type="switch">
		<connection interface="ovz1.eth2" lossratio="0.1" delay="50" bandwidth="200"/>
		<connection interface="kvm1.eth2"/>
	</connector>
	<connector name="router1" type="router">
		<connection interface="ovz1.eth3" gateway="10.1.1.254/24" lossratio="0.1" delay="50" bandwidth="200"/>
		<connection interface="kvm1.eth3" gateway="10.1.2.254/24"/>
	</connector>
</topology>
'''

class Test(unittest.TestCase):

	def setUp(self):
		tests.default_setUp()
		
 	def tearDown(self):
		tests.default_tearDown()

	def testImport(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		assert id
		list = api.top_list("*", "*", "*", user=admin)
		assert len(list) == 1
		assert list[0]["name"] == "test1"

	def testExport(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		assert len(api.top_get(id, user=admin)) > 100

	def testInfo(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		info = api.top_info(id, user=admin)
		assert info["id"] == id
		assert info["name"] == "test1"
		assert info["owner"] == "admin"
		assert info["analysis"]["problems"] == []
		assert info["analysis"]["warnings"] == []
		self.assertEquals(len(info["analysis"]["hints"]),2)
		assert info["device_count"] == 2
		assert info["connector_count"] == 4

	def testLifecycle(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		api.top_prepare(id, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_start(id, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_stop(id, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_destroy(id, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_start(id, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_destroy(id, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_remove(id, user=admin)
		tests.wait_for_tasks(api, admin)