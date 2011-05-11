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

import os
os.environ['TOMATO_TESTING']="true"

def wait_for_tasks(api, user):
	import time
	while tasks_running(api, user):
		time.sleep(0.1)
	
def tasks_running(api, user):
	count=0
	for t in api.task_list(user=user):
		if t["active"]:
			count+=1
	return count

def default_setUp():
	import tomato as api
	admin = api.login("admin", "123")
	api.host_add("host1a", "group1", True, {"vmid_start": 1000, "vmid_count": 200, "port_start": 7000, "port_count": 1000, "bridge_start": 1000, "bridge_count": 1000}, user=admin)
	api.host_add("host1b", "group1", True, {"vmid_start": 1000, "vmid_count": 200, "port_start": 7000, "port_count": 1000, "bridge_start": 1000, "bridge_count": 1000}, user=admin)
	api.host_add("host2a", "group2", True, {"vmid_start": 1000, "vmid_count": 200, "port_start": 7000, "port_count": 1000, "bridge_start": 1000, "bridge_count": 1000}, user=admin)
	api.host_add("host2b", "group2", True, {"vmid_start": 1000, "vmid_count": 200, "port_start": 7000, "port_count": 1000, "bridge_start": 1000, "bridge_count": 1000}, user=admin)
	api.host_add("host2c", "group2", True, {"vmid_start": 1000, "vmid_count": 200, "port_start": 7000, "port_count": 1000, "bridge_start": 1000, "bridge_count": 1000}, user=admin)
	api.template_add("tpl_openvz_1", "openvz", "", user=admin)
	api.template_add("tpl_openvz_2", "openvz", "", user=admin)
	api.template_set_default("openvz", "tpl_openvz_1", user=admin)
	api.template_add("tpl_kvm_1", "kvm", "", user=admin)
	api.template_add("tpl_kvm_2", "kvm", "", user=admin)
	api.template_set_default("kvm", "tpl_kvm_1", user=admin)
	api.external_network_add("internet", "test", {}, user=admin)
	api.external_network_bridge_add("host1a", "internet", "test", "vmbr0", user=admin)
	wait_for_tasks(api, admin)
	
def default_tearDown():
	import tomato as api
	admin = api.login("admin", "123")
	for top in api.top_list("", "", "", user=admin):
		api.top_action(top["id"], "topology", None, "remove", direct=True, user=admin)
	for host in api.host_list("", user=admin):
		api.host_remove(host["name"], user=admin)
	for template in api.template_list("", user=admin):
		api.template_remove(template["name"], user=admin)
	for en in api.externalNetworks(user=admin):
		api.external_network_remove(en["type"], en["group"], user=admin)
		
def encode_mod(type, element, subelement, properties):
	return {"type": type, "element": element, "subelement": subelement, "properties": properties}

import hosts, templates, kvm, openvz, tinc, topology, tasks
