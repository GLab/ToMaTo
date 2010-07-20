# -*- coding: utf-8 -*-

from glabnetem.topology import *
from glabnetem.topology_store import *
from glabnetem.openvz_device import *
from glabnetem.resource_store import *
from glabnetem.host_store import *
from glabnetem.host import *

top = TopologyStore.get(1)
top.deploy()
