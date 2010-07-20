# -*- coding: utf-8 -*-

from glabnetem.topology import *
from glabnetem.openvz_device import *
from glabnetem.resource_store import *
from glabnetem.host_store import *
from glabnetem.host import *

ResourceStore.topology_ids = ResourceStore ( 1, 10000 )
OpenVZDevice.set_openvz_ids ( "host1", ResourceStore ( 1000, 100 ) )
OpenVZDevice.set_openvz_ids ( "host2", ResourceStore ( 1000, 100 ) )
OpenVZDevice.set_openvz_ids ( "host3", ResourceStore ( 1000, 100 ) )
OpenVZDevice.set_openvz_ids ( "host4", ResourceStore ( 1000, 100 ) )
HostStore.add ( Host("host1") )
HostStore.add ( Host("host2") )
HostStore.add ( Host("host3") )
HostStore.add ( Host("host4") )

top = Topology("example.xml") 
top.output()
top.take_resources()
top.save_to("example2.xml") 
top.write_deploy_scripts()
