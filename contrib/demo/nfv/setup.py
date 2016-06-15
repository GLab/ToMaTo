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
	parser.add_argument("--site", required=False, help="site for elements")
	parser.add_argument("--html", required=False, help="if set, create a demo html client file for this.")
	parser.add_argument("--skip-software", action="store_true", default=False, help="when set, no additional software will be installed. Only useful in combination with --topology")
	parser.add_argument("arguments", nargs="*", help="python code to execute directly")
	options = parser.parse_args()
	if not options.username and not (options.client_cert or options.url):
		options.username = raw_input("Username: ")
	if not options.password and not (options.client_cert or options.url):
		options.password = getpass.getpass("Password: ")
	if options.ssl and options.protocol == "http+xmlrpc":
		options.protocol = "https+xmlrpc"
	return options




def import_topology_and_get_config(api, site=None):
	print "creating topology"
	with open("nfv_demo.tomato4.json") as f:
		to_import = json.load(f)
	top_id, _, _, _ = api.topology_import(to_import)
	if site is not None:
		top_info = api.topology_info(top_id, True)
		for element in top_info["elements"]:
			try:
				api.element_modify(element["id"], {"site": site})
			except:
				pass
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
		return import_topology_and_get_config(api, options.site)
	else:
		return examine_topology_and_get_config(api, options.topology), options.topology

def create_html(options, config, topology_id):
	"""
	Create the html file if required.
	:param options: parsed program arguments
	:param config: config from get_config
	:param topology_id: topology ID of target topology
	:return: URL to HTML file, or None, depending on whether the HTML file should be created.
	:rtype: str or NoneType
	"""
	if options.html is None:
		return None
	with open(os.path.join("gui", "nfv_demo.html"), "r") as f:
		htmlcontent = f.read()
	for name, info in config.iteritems():
		htmlcontent = htmlcontent.replace(
		  '<iframe class="vnc" id="%s" src="request.html"></iframe>' % name,
			'<iframe class="vnc" id="%s" src="http://%s/element/%s/console_novnc"></iframe>' % (name, options.hostname, info["element_id"])
		)
	htmlcontent = htmlcontent.replace("</body>", '<a style="color:black;position:absolute;bottom:0;" href="http://%s/topology/%s" target="_blank">Open Editor</a></body>' % (options.hostname, topology_id))
	htmlcontent = htmlcontent.replace("topology.png", os.path.basename(options.html)+".topology.png")
	htmldir = os.path.abspath(os.path.dirname(options.html))
	if not os.path.exists(htmldir):
		os.makedirs(htmldir)
	shutil.copy(os.path.join("gui", "topology.png"), os.path.join(htmldir, os.path.basename(options.html)+".topology.png"))
	with open(options.html, "w+") as f:
		f.write(htmlcontent)
	return os.path.abspath(options.html)



options = parseArgs()
url = options.url if options.url else createUrl(options.protocol, options.hostname, options.port, options.username, options.password)
api = getConnection(url, options.client_cert)

config, top_id = get_config(options, api)


if not options.skip_software:

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

htmlfile = create_html(options, config, top_id)

print ""
print "Configuration complete"
print ""
print "IDs:"
print "  topology:", top_id
for name, info in config.iteritems():
	print "  "+name+":", info["element_id"]
print ""
print "Topology is probably available at"
print "  http://%s/topology/%s" % (options.hostname, top_id)

if htmlfile:
	print ""
	print "HTML client file available at:"
	print "  file://"+htmlfile

print ""
print "To complete setup, please run these commands on the OpenFlow switch:"
print "  address 10.0.0.100"
print "  ovs-vsctl set-fail-mode br0 standalone"
print "  ovs-vsctl set-controller br0 tcp:10.0.0.3:6633"