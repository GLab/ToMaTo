# -*- coding: utf-8 -*-

from glabnetem.topology import *
from glabnetem.topology_store import *
from glabnetem.openvz_device import *
from glabnetem.resource_store import *
from glabnetem.host_store import *
from glabnetem.host import *

for host in HostStore.hosts.values():
	print host.name
	print host.ports.resources
	print host.openvz_ids.resources
	print host.bridge_ids.resources


# ./ipfw add pipe 1 via gbr1004 out
# ./ipfw pipe 1 config delay 200ms

# ./ipfw delete 100