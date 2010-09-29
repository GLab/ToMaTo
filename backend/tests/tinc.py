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
	<device id="openvz1" type="openvz" root_password="test123">
		<interface id="eth0" use_dhcp="true"/>
		<interface id="eth1" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
		<interface id="eth2" use_dhcp="true"/>
	</device>
	<device id="kvm1" type="kvm">
		<interface id="eth0"/>
		<interface id="eth1"/>
	</device>
	<connector id="switch1" type="switch">
		<connection device="openvz1" interface="eth0"/>
		<connection device="kvm1" interface="eth0"/>
	</connector> 
	<connector id="router1" type="router">
		<connection device="openvz1" interface="eth1" gateway="10.1.1.254/24"/>
		<connection device="kvm1" interface="eth1" gateway="10.1.2.254/24"/>
	</connector> 
</topology>
'''

TOP2 = '''
<topology name="test1">
	<device id="openvz1" type="openvz" root_password="test123">
		<interface id="eth0" use_dhcp="true"/>
		<interface id="eth1" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
		<interface id="eth2" use_dhcp="true"/>
	</device>
	<device id="kvm1" type="kvm">
		<interface id="eth0"/>
		<interface id="eth1"/>
	</device>
	<connector id="switch1" type="switch">
		<connection device="openvz1" interface="eth2"/>
		<connection device="kvm1" interface="eth0"/>
	</connector> 
	<connector id="router1" type="router">
		<connection device="openvz1" interface="eth1" gateway="10.1.2.254/24"/>
		<connection device="kvm1" interface="eth1" gateway="10.1.1.254/24"/>
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

	def testLifecycle(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		api.connector_prepare(id, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_start(id, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_stop(id, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_destroy(id, "switch1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_prepare(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_start(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_stop(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_destroy(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)

	def testChange(self):
		admin = api.login("admin", "123")
		id = api.top_import(TOP1, user=admin)
		api.top_change(id, TOP2, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP1, user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_prepare(id, "switch1", user=admin)
		api.connector_prepare(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP2, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP1, user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_start(id, "switch1", user=admin)
		api.connector_start(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP2, user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_change(id, TOP1, user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_stop(id, "switch1", user=admin)
		api.connector_stop(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
		api.connector_destroy(id, "switch1", user=admin)
		api.connector_destroy(id, "router1", user=admin)
		tests.wait_for_tasks(api, admin)
