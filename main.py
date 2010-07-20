# -*- coding: utf-8 -*-

from glabnetem.topology_store import *
from glabnetem.topology import *

import sys

def usage(argv):
	print """Glab NetEm control tool

topology SUBCOMMAND [options]
	list
	print ID
	import FILE
	export ID FILE
	remove ID
	deploy ID
	create ID
	destroy ID
	start ID
	stop ID
host SUBCOMMAND [options]
	list
	add NAME
	remove NAME
"""

def topology(argv):
	if len(argv) == 0:
		usage(None)
		return
	{"import": topology_import, "export": topology_export, "print": topology_print,
	"remove": topology_remove, "deploy": topology_deploy, "create": topology_create,
	"destroy": topology_destroy, "start": topology_start, 
	"stop": topology_stop, "list": topology_list}.get(argv[0],usage)(argv[1:])

def topology_list(argv):
	if not len(argv) == 0:
		usage(None)
		return
	for top in TopologyStore.topologies.values():
		print top.id

def topology_import(argv):
	if not len(argv) == 1:
		usage(None)
		return
	print "Created ID %s " % TopologyStore.add(Topology(argv[0]))

def topology_export(argv):
	if not len(argv) == 2:
		usage(None)
		return
	TopologyStore.get(int(argv[0])).save_to(argv[1])

def topology_print(argv):
	if not len(argv) == 1:
		usage(None)
		return
	TopologyStore.get(int(argv[0])).output()

def topology_remove(argv):
	if not len(argv) == 1:
		usage(None)
		return
	TopologyStore.remove(int(argv[0]))

def topology_deploy(argv):
	if not len(argv) == 1:
		usage(None)
		return
	TopologyStore.get(int(argv[0])).deploy()

def topology_create(argv):
	if not len(argv) == 1:
		usage(None)
		return
	TopologyStore.get(int(argv[0])).create()

def topology_destroy(argv):
	if not len(argv) == 1:
		usage(None)
		return
	TopologyStore.get(int(argv[0])).destroy()

def topology_start(argv):
	if not len(argv) == 1:
		usage(None)
		return
	TopologyStore.get(int(argv[0])).start()

def topology_stop(argv):
	if not len(argv) == 1:
		usage(None)
		return
	TopologyStore.get(int(argv[0])).stop()

def host(argv):
	if len(argv) == 0:
		usage(None)
		return
	{"list": host_list, "add": host_add, "remove": host_remove}.get(argv[0],usage)(argv[1:])

def host_list(argv):
	if not len(argv) == 0:
		usage(None)
		return
	for host in HostStore.hosts.values():
		print host.name

def host_add(argv):
	if not len(argv) == 1:
		usage(None)
		return
	HostStore.add(argv[0])

def host_remove(argv):
	if not len(argv) == 1:
		usage(None)
		return
	HostStore.remove(argv[0])

def main(argv):
	if len(argv) == 0:
		usage(None)
		return
	{"topology": topology, "host": host}.get(argv[0],usage)(argv[1:])

if __name__ == "__main__":
    main(sys.argv[1:])