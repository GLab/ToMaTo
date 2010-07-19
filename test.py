# -*- coding: utf-8 -*-

from glabnetem.topology import *
from glabnetem.openvz_device import *
from glabnetem.resource_store import *

OpenVZDevice.set_openvz_ids ( "host1", ResourceStore ( 1000, 100 ) )
OpenVZDevice.set_openvz_ids ( "host2", ResourceStore ( 1000, 100 ) )
OpenVZDevice.set_openvz_ids ( "host3", ResourceStore ( 1000, 100 ) )
OpenVZDevice.set_openvz_ids ( "host4", ResourceStore ( 1000, 100 ) )
ResourceStore.host_ports["host1"] = ResourceStore ( 5000, 1000 )
ResourceStore.host_ports["host2"] = ResourceStore ( 5000, 1000 )
ResourceStore.host_ports["host3"] = ResourceStore ( 5000, 1000 )
ResourceStore.host_ports["host4"] = ResourceStore ( 5000, 1000 )

top = Topology("example.xml") 
top.output()
top.take_resources()
top.deploy()
