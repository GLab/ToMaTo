#!/usr/bin/python
# -*- coding: utf-8 -*-    

TOP1='''
<topology name="test1">
    <device id="ovz1" type="openvz" root_password="test">
        <interface id="eth0" use_dhcp="true"/>
        <interface id="eth1" ip4address="10.1.1.1" ip4netmask="10.1.1.1"/>
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
        <connection device="ovz1" interface="eth1" lossratio="0.1" delay="50ms" bandwidth="200k"/>
        <connection device="kvm1" interface="eth1"/>
    </connector>
</topology>
'''


import glabnetman as api

admin=api.login("admin","123")

assert api.host_list("*", user=admin) == []

api.host_add("host1a", "group1", "vmbr0", user=admin)
api.host_add("host1b", "group1", "vmbr0", user=admin)
api.host_add("host2a", "group2", "vmbr0", user=admin)
api.host_add("host2b", "group2", "vmbr0", user=admin)
api.host_add("host2c", "group2", "vmbr0", user=admin)

assert len(api.host_list("*", user=admin)) == 5
assert len(api.host_list("group1", user=admin)) == 2
assert len(api.host_list("group2", user=admin)) == 3

api.host_remove("host2c", user=admin)
assert len(api.host_list("group2", user=admin)) == 2


assert api.top_list("*", "*", "*", user=admin) == []

api.top_import(TOP1, user=admin)
assert len(api.top_list("*", "*", "*", user=admin)) == 1

api.top_get(1, user=admin)

print api.top_info(1, user=admin)