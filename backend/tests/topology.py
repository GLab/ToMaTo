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
import glabnetman as api

TOP1 = '''
<topology name="test1">
	<device id="ovz1" type="openvz" root_password="test">
		<interface id="eth0" use_dhcp="true"/>
		<interface id="eth1" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
		<interface id="eth2" use_dhcp="true"/>
		<interface id="eth3" use_dhcp="true"/>
	</device>
	<device id="kvm1" type="kvm">
		<interface id="eth0"/>
		<interface id="eth1"/>
		<interface id="eth2"/>
		<interface id="eth3"/>
	</device>
	<connector id="internet" type="real">
		<connection device="ovz1" interface="eth0"/>
		<connection device="kvm1" interface="eth0"/>
	</connector>
	<connector id="hub1" type="hub">
		<connection device="ovz1" interface="eth1" lossratio="0.1" delay="50" bandwidth="200"/>
		<connection device="kvm1" interface="eth1"/>
	</connector>
		<connector id="switch1" type="switch">
				<connection device="ovz1" interface="eth2" lossratio="0.1" delay="50" bandwidth="200"/>
				<connection device="kvm1" interface="eth2"/>
		</connector>
		<connector id="router1" type="router">
				<connection device="ovz1" interface="eth3" gateway="10.1.1.254/24" lossratio="0.1" delay="50" bandwidth="200"/>
				<connection device="kvm1" interface="eth3" gateway="10.1.2.254/24"/>
		</connector>
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

	def testImport(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		assert id
		list = api.top_list("*", "*", user=admin)
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