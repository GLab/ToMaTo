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
	tests.encode_mod("device-create", None, None, {"name": "kvm1", "type": "kvm"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth0"}),
	tests.encode_mod("interface-create", "kvm1", None, {"name": "eth1"}),
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
		api.top_action(tid, "device", "kvm1", "prepare", direct=True, user=admin)
		api.top_action(tid, "device", "kvm1", "start", direct=True, user=admin)
		api.top_action(tid, "device", "kvm1", "stop", direct=True, user=admin)
		api.top_action(tid, "device", "kvm1", "destroy", direct=True, user=admin)

	def testChange(self):
		admin = api.login("admin", "123")
		tid = api.top_create(user=admin)
		api.top_modify(tid, TOP1, direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-rename", "kvm1", None, {"name": "kvm2"})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-configure", "kvm2", None, {"hostgroup": "test"})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-delete", "kvm2", None, {})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("device-create", None, None, {"type": "kvm", "name": "kvm1"})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("interface-create", "kvm1", None, {"name": "eth0"})], direct=True, user=admin)
		api.top_modify(tid, [tests.encode_mod("interface-delete", "kvm1", "eth0", {})], direct=True, user=admin)
		