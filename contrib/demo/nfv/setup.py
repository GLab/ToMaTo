#!/usr/bin/python

import os
import argparse
import getpass
import json
import random
import shutil
import tarfile

from lib import getConnection, createUrl
from lib.upload_download import upload_and_use_rextfv


def parseArgs():
	"""
	Defines required and optional arguments for the cli and parses them out of sys.argv.

	Available Arguments are:
		Argument *--help*:
			Prints a help text for the available arguments
		Argument *--url*:
			The whole URL of the server
		Argument *--protocol*:
			Protocol of the server
		Argument *--hostname*:
			Address of the host of the server
		Argument *--port*:
			Port of the host server
		Argument *--ssl*:
			Whether to use ssl or not
		Argument *--client_cert*:
			Path to the ssl certificate of the client
		Argument *--username*:
			The username to use for login
		Argument *--password*:
			The password to user for login
		Argument *--file*:
			Path to a file to execute
		Argument *arguments*
			Python code to execute directly

	Return value:
		Parsed command-line arguments

	"""
	parser = argparse.ArgumentParser(description="ToMaTo RPC Client", add_help=False)
	parser.add_argument('--help', action='help')
	parser.add_argument("--url", "-u", required=False, help="the whole URL of the server")
	parser.add_argument("--protocol", required=False, default="http+xmlrpc", help="the protocol of the server")
	parser.add_argument("--hostname", "-h", required=False, help="the host of the server")
	parser.add_argument("--port", "-p", default=8000, help="the port of the server")
	parser.add_argument("--ssl", "-s", action="store_true", default=False, help="whether to use ssl")
	parser.add_argument("--client_cert", "-c", required=False, default=None, help="path of the ssl certificate")
	parser.add_argument("--username", "-U", help="the username to use for login")
	parser.add_argument("--password", "-P", help="the password to use for login")
	parser.add_argument("--file", "-f", help="a file to execute")
	parser.add_argument("--topology", "-t", required=False, help="ID of the topology to use. If not set, a new topology will be created")
	parser.add_argument("arguments", nargs="*", help="python code to execute directly")
	options = parser.parse_args()
	if not options.username and not (options.client_cert or options.url):
		options.username = raw_input("Username: ")
	if not options.password and not (options.client_cert or options.url):
		options.password = getpass.getpass("Password: ")
	if options.ssl and options.protocol == "http+xmlrpc":
		options.protocol = "https+xmlrpc"
	return options




def import_topology_and_get_config(api):
	print "creating topology"
	with open("nfv_demo.tomato4.json") as f:
		to_import = json.load(f)
	top_id, _, _, _ = api.topology_import(to_import)
	return examine_topology_and_get_config(api, top_id), top_id


def examine_topology_and_get_config(api, topology_id):
	print "starting topology"
	api.topology_action(topology_id, "start")

	print "analyzing topology"

	top_info = api.topology_info(topology_id, True)
	element_infos = {}
	for element in top_info["elements"]:
		element_infos[element['id']] = element

	preresult = {}
	for connection in top_info["connections"]:
		if_router, if_host = None, None
		for elem_id in connection["elements"]:
			info = element_infos[elem_id]
			if info["type"] == "kvmqm_interface":
				if_router = elem_id
			else:
				if_host = elem_id
		elem_id = element_infos[if_host]["parent"]
		elem_name = element_infos[elem_id]["name"].lower()
		preresult[elem_name] = {
			"if_router": if_router,
			"if_elem": if_host,
			"elem_id": elem_id
		}

	result = {}
	for name, info in preresult.iteritems():
		result[name] = {
			"ip": element_infos[info["if_elem"]]["ip4address"].split("/")[0],
			"mac": element_infos[info["if_elem"]]["mac"],
			"router_if": element_infos[info["if_router"]]["name"],
			"element_id": info["elem_id"]
		}
	return result

def get_config(options, api):
	"""
	read the existing topology, or create a new one.
	return the config.
	the config will contain four keys: "sender", "receiver", "compressor", "controller"
	each of these contains "ip", "mac", "router_if", "element_id"

	:param api: API proxy
	:param options: parsed program arguments
	:return: config as described
	:rtype: dict
	"""
	if options.topology is None:
		return import_topology_and_get_config(api)
	else:
		return examine_topology_and_get_config(api, options.topology), None



options = parseArgs()
url = options.url if options.url else createUrl(options.protocol, options.hostname, options.port, options.username, options.password)
api = getConnection(url, options.client_cert)

config, top_id = get_config(options, api)

randint = random.randint(0, 100000)
while os.path.exists(os.path.join("/tmp", "tomato_demo_setup_%d" % randint)):
	randint = random.randint(0, 100000)
installer_dir = os.path.join("/tmp", "tomato_demo_setup_%d" % randint)
installer_archive = os.path.join(installer_dir, "install_demo.tar.gz")

shutil.copytree("archive_content", installer_dir)
with open(os.path.join(installer_dir, "config.json"), "w+") as f:
	json.dump(config, f)
with tarfile.open(installer_archive, 'w:gz') as tar:
	tar.add(installer_dir, arcname='.')

for name, inf in config.iteritems():
	print "Installing software on '%s'" % name
	print "  python"
	upload_and_use_rextfv(api, inf["element_id"], "install_python.tar.gz", True)
	print "  demo software"
	upload_and_use_rextfv(api, inf["element_id"], installer_archive, True)

shutil.rmtree(installer_dir)

if top_id is not None:
	print "New topology's ID is [%s]"
	print "Probably available at http://%s/topology/%s" % (options.hostname, top_id)