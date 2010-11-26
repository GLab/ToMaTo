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
	<device name="kvm1" type="kvm">
		<interface name="eth0"/>
		<interface name="eth1"/>
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
		api.top_modify(id, tests.encode_modification("device-rename", "kvm1", None, {"name": "kvm2"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(id, tests.encode_modification("device-configure", "kvm2", None, {"hostgroup": "test"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(id, tests.encode_modification("device-delete", "kvm2", None, {}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(id, tests.encode_modification("device-create", None, None, {"type": "kvm", "name": "kvm1"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(id, tests.encode_modification("interface-create", "kvm1", None, {"name": "eth0"}), user=admin)
		tests.wait_for_tasks(api, admin)
		api.top_modify(id, tests.encode_modification("interface-configure", "kvm1", "eth0", {}), user=admin)
		tests.wait_for_tasks(api, admin)
		#api.top_modify(id, tests.encode_modification("interface-rename", "kvm1", "eth0", {"name": "eth1"}), user=admin)
		#tests.wait_for_tasks(api, admin)
		api.top_modify(id, tests.encode_modification("interface-delete", "kvm1", "eth0", {}), user=admin)
		tests.wait_for_tasks(api, admin)
		