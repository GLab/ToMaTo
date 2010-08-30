'''
Created on Aug 30, 2010

@author: lemming
'''
import unittest
import time
import glabnetman as api

TOP1='''
<topology name="test1">
    <device id="ovz1" type="openvz" root_password="test">
        <interface id="eth0" use_dhcp="true"/>
        <interface id="eth1" ip4address="10.1.1.1/24" gateway="10.1.1.254"/>
    </device>
    <device id="kvm1" type="kvm">
        <interface id="eth0"/>
        <interface id="eth1"/>
    </device>
    <connector id="internet" type="real">
        <connection device="ovz1" interface="eth0"/>
        <connection device="kvm1" interface="eth0"/>
    </connector>
    <connector id="tinc1" type="switch">
        <connection device="ovz1" interface="eth1" lossratio="0.1" delay="50" bandwidth="200"/>
        <connection device="kvm1" interface="eth1"/>
    </connector>
</topology>
'''

class Test(unittest.TestCase):

    def setUp(self):
        admin=api.login("admin","123")
        api.host_add("host1a", "group1", "vmbr0", user=admin)
        api.host_add("host1b", "group1", "vmbr0", user=admin)
        api.host_add("host2a", "group2", "vmbr0", user=admin)
        api.host_add("host2b", "group2", "vmbr0", user=admin)
        api.template_add("tpl_openvz_1", "openvz", admin)
        api.template_add("tpl_openvz_2", "openvz", admin)
        api.template_set_default("openvz", "tpl_openvz_1", admin)
        api.template_add("tpl_kvm_1", "kvm", admin)
        api.template_add("tpl_kvm_2", "kvm", admin)
        api.template_set_default("kvm", "tpl_kvm_1", admin)
        
    def tearDown(self):
        admin=api.login("admin","123")
        for top in api.top_list("*", "*", admin):
            api.top_remove(top["id"], admin)
        for host in api.host_list("*", admin):
            api.host_remove(host["name"], admin)
        for template in api.template_list("*", admin):
            api.template_remove(template["name"], admin)

    def testSimple(self):
        admin=api.login("admin","123")
        assert api.top_list("*", "*", user=admin) == []
        api.top_import(TOP1, user=admin)
        assert len(api.top_list("*", "*", user=admin)) == 1
        api.top_get(1, user=admin)
        api.top_info(1, user=admin)
        api.top_prepare(1, user=admin)
        time.sleep(0.1)
        api.top_start(1, user=admin)
        time.sleep(0.1)
        api.top_stop(1, user=admin)
        time.sleep(0.1)
        api.top_destroy(1, user=admin)
        time.sleep(0.1)
        api.top_remove(1, user=admin)
        assert api.top_list("*", "*", user=admin) == []