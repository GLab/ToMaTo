#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, xmlrpclib, getpass

user=raw_input("Username: ")
password=getpass.getpass("Password: ")
api=xmlrpclib.ServerProxy('http://%s:%s@localhost:8000' % (user, password) )

def usage(argv):
	print """Glab NetEm control tool

topology SUBCOMMAND [options]
	list
	print ID
	import FILE
	export ID FILE
	status ID
	remove ID
	upload ID
	prepare ID
	destroy ID
	start ID
	stop ID
host SUBCOMMAND [options]
	list
	add NAME
	remove NAME
	check NAME
"""

def topology(argv):
	if len(argv) == 0:
		usage(None)
		return
	{"import": topology_import, "export": topology_export, "print": topology_print,
	"remove": topology_remove, "upload": topology_upload, "prepare": topology_prepare,
	"destroy": topology_destroy, "start": topology_start, "stop": topology_stop,
	"list": topology_list, "status": topology_status}.get(argv[0],usage)(argv[1:])

def topology_list(argv):
	if not len(argv) == 0:
		usage(None)
		return
	for top in api.top_list():
		print top['id'], top['state']

def topology_import(argv):
	if not len(argv) == 1:
		usage(None)
		return
	xml="".join(open(argv[0],"r").readlines())
	id=api.top_import(xml)
	print "Created ID %s " % id

def topology_export(argv):
	if not len(argv) == 2:
		usage(None)
		return
	xml=api.top_get(int(argv[0]))
	fd=open ( argv[1], "w" )
	fd.write(xml)
	fd.close()

def topology_print(argv):
	if not len(argv) == 1:
		usage(None)
		return
	print api.top_get(int(argv[0]))

def topology_status(argv):
	if not len(argv) == 1:
		usage(None)
		return
	print api.top_info(int(argv[0])).state

def topology_remove(argv):
	if not len(argv) == 1:
		usage(None)
		return
	print api.top_remove(int(argv[0]))

def topology_upload(argv):
	if not len(argv) == 1:
		usage(None)
		return
	api.top_upload(int(argv[0]))

def topology_prepare(argv):
	if not len(argv) == 1:
		usage(None)
		return
	api.top_prepare(int(argv[0]))

def topology_destroy(argv):
	if not len(argv) == 1:
		usage(None)
		return
	api.top_destroy(int(argv[0]))

def topology_start(argv):
	if not len(argv) == 1:
		usage(None)
		return
	api.top_start(int(argv[0]))

def topology_stop(argv):
	if not len(argv) == 1:
		usage(None)
		return
	api.top_stop(int(argv[0]))

def host(argv):
	if len(argv) == 0:
		usage(None)
		return
	{"list": host_list, "add": host_add, "remove": host_remove}.get(argv[0],usage)(argv[1:])

def host_list(argv):
	if not len(argv) == 0:
		usage(None)
		return
	for host in api.host_list():
		print host['name']

def host_add(argv):
	if not len(argv) == 1:
		usage(None)
		return
	api.host_add(argv[0])

def host_remove(argv):
	if not len(argv) == 1:
		usage(None)
		return
	api.host_remove(argv[0])

def main(argv):
	if len(argv) == 0:
		usage(None)
		return
	{"topology": topology, "host": host}.get(argv[0],usage)(argv[1:])

if __name__ == "__main__":
	#try:
	main(sys.argv[1:])
	#except Exception as ex:
	#	print ex
