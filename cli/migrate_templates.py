#!/usr/bin/python

from lib import getConnection, createUrl
from lib.error import TransportError
import argparse, getpass, datetime, time

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

	parser.add_argument("--url_source" , "-su", required=False, help="the whole URL of the source server")
	parser.add_argument("--protocol_source", required=False, default="http+xmlrpc", help="the protocol of the source server")
	parser.add_argument("--hostname_source", "-sh", required=False, help="the host of the source server")
	parser.add_argument("--port_source", "-sp", default=8000, help="the port of the source server")
	parser.add_argument("--ssl_source", "-ss", action="store_true", default=False, help="whether to use ssl on source server")
	parser.add_argument("--client_cert_source", "-sc", required=False, default=None, help="path of the ssl certificate to use for source server")
	parser.add_argument("--username_source", "-sU", help="the username to use for login on source server")
	parser.add_argument("--password_source", "-sP", help="the password to use for login on source server")

	parser.add_argument("--url_destination" , "-du", required=False, help="the whole URL of the destination server")
	parser.add_argument("--protocol_destination", required=False, default="http+xmlrpc", help="the protocol of the destination server")
	parser.add_argument("--hostname_destination", "-dh", required=False, help="the host of the destination server")
	parser.add_argument("--port_destination", "-dp", default=8000, help="the port of the destination server")
	parser.add_argument("--ssl_destination", "-ds", action="store_true", default=False, help="whether to use ssl on destination server")
	parser.add_argument("--client_cert_destination", "-dc", required=False, default=None, help="path of the ssl certificate to use for destination server")
	parser.add_argument("--username_destination", "-dU", help="the username to use for login on destination server")
	parser.add_argument("--password_destination", "-dP", help="the password to use for login on destination server")

	parser.add_argument("--no-keyring", default=False, action="store_true", help="ignore passwords from keyring")
	parser.add_argument("--include_restricted", default=False, help="whether to include restricted templates")
	parser.add_argument("--templates", "-t", metavar='T', nargs="+", default=None, help="only migrate templates with this name")
	parser.add_argument("--overwrite_on_conflict", default=False, action="store_true", help="in case of conflict, overwrite the template (default: ignore)")

	parser.add_argument("arguments", nargs="*", help="python code to execute directly")
	options = parser.parse_args()

	if not options.no_keyring:
		try:
			import keyring
			KEYRING_SERVICE_NAME = "ToMaTo"

			if options.username_source and not (options.password_source or options.client_cert_source):
				KEYRING_USER_NAME = "%s/%s" % (options.hostname_source, options.username_source)
				options.password_source = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USER_NAME)
			if options.username_destination and not (options.password_destination or options.client_cert_destination):
				KEYRING_USER_NAME = "%s/%s" % (options.hostname_destination, options.username_destination)
				options.password_destination = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USER_NAME)

		except ImportError:
			pass


	need_source_username = not options.username_source and not options.client_cert_source
	need_source_password = not options.password_source and not options.client_cert_source
	need_destination_username = not options.username_destination and not options.client_cert_destination
	need_destination_password = not options.password_destination and not options.client_cert_destination

	if need_source_username or need_source_password:
		print "Login data to source backend"
	if need_source_username:
		options.username_source=raw_input(" Username for %s: " % options.hostname_source)
	if need_source_password:
		options.password_source= getpass.getpass(" Password for %s: " % options.hostname_source)
	if options.ssl_source and options.protocol_source == "http+xmlrpc":
		options.protocol_source = "https+xmlrpc"

	if need_destination_username or need_destination_password:
		print ""
		print "Login data to destination backend"
	if need_destination_username:
		options.username_destination=raw_input(" Username for %s: " % options.hostname_destination)
	if need_destination_password:
		options.password_destination= getpass.getpass(" Password for %s: " % options.hostname_destination)
	if options.ssl_destination and options.protocol_destination == "http+xmlrpc":
		options.protocol_destination = "https+xmlrpc"

	return options

def _read_templates_4_0_2(api, include_restricted, template_names):
	results = []
	templates = api.template_list()
	for t in templates:
		if include_restricted or not t.get('restricted', False):
			if template_names is None or t['name'] in template_names:
				for k in ("all_urls", "popularity", "kblang", "checksum", "ready", "size", "id"):
					del t[k]
				if t["tech"] == "kvmqm":
					t["tech"] = "full"
				elif t["tech"] == "openvz":
					t["tech"] = "container"
				results.append(t)
	return results

def _read_templates_4_1_0(api, include_restricted, template_names):
	results = []
	templates = api.template_list()
	for t in templates:
		if include_restricted or not t.get('restricted', False):
			if template_names is None or t['name'] in template_names:
				for k in ("all_urls", "popularity", "kblang", "checksum", "ready", "size", "id"):
					del t[k]
				results.append(t)
	return results

def _insert_template_4_0_2(api, template, overwrite_on_conflict):
	try:
		if template["tech"] == "full":
			template["tech"] = "kvmqm"
		elif template["tech"] == "container":
			template["tech"] = "openvz"
		t = api.template_create(template['tech'], template['name'], {k: v for k, v in template.iteritems() if k not in ("tech", "name")})
		templ_id = t['id']
	except Exception, e:  # something went wrong.
		if not overwrite_on_conflict:  # if we don't want to overwrite this, abort.
			raise e
		try:  # let's see whether this template exists. if yes, just overwrite it. otherwise, abort.
			templates = api.template_list(template['tech'])
			for t in templates:
				if t['name'] == template['name'] and t['tech'] == template['tech']:
					templ_id = t['id']
		except:
			raise e

def _insert_template_4_1_0(api, template, overwrite_on_conflict):
	try:
		t = api.template_create(template['tech'], template['name'], {k: v for k, v in template.iteritems() if k not in ("tech", "name")})
		templ_id = t['id']
	except Exception, e:  # something went wrong.
		if not overwrite_on_conflict:  # if we don't want to overwrite this, abort.
			raise e
		try:  # let's see whether this template exists. if yes, just overwrite it. otherwise, abort.
			templates = api.template_list(template['tech'])
			for t in templates:
				if t['name'] == template['name'] and t['tech'] == template['tech']:
					templ_id = t['id']
		except:
			raise e


def read_templates(api, version, include_restricted, template_names):
	if version not in [[4, 0, 2], [4, 1, 0]]:
		print "unsupported source version: %s.%s.%s" % (version[0], version[1], version[2])
		return []

	elif version[0] == 4:
		if version[1] == 0:
			return _read_templates_4_0_2(api, include_restricted, template_names)
		else:
			return _read_templates_4_1_0(api, include_restricted, template_names)

def insert_template(api, version, template, overwrite_on_conflict):
	if version not in [[4, 0, 2], [4, 1, 0]]:
		print "unsupported destination version: %s.%s.%s" % (version[0], version[1], version[2])
		return

	elif version[0] == 4:
		if version[1] == 0:
			return _insert_template_4_0_2(api, template, overwrite_on_conflict)
		else:
			return _insert_template_4_1_0(api, template, overwrite_on_conflict)




options = parseArgs()

print ""
print "testing connection to source backend..."
try:
	if options.url_source:
		url_source = options.url_source
	else:
		url_source = createUrl(options.protocol_source, options.hostname_source, options.port_source, options.username_source, options.password_source)
	api_source = getConnection(url_source, options.client_cert_source)
	source_version = api_source.server_info().get('api_version', [3, 0, 0])
	print " Success"
except TransportError as e:
	print " ERROR:", e.message
	exit(1)
except:
	print " ERROR"
	print ""
	raise

print ""
print "testing connection to destination backend..."
try:
	if options.url_destination:
		url_destination = options.url_destination
	else:
		url_destination = createUrl(options.protocol_destination, options.hostname_destination, options.port_destination, options.username_destination, options.password_destination)
	api_destination = getConnection(url_destination, options.client_cert_destination)
	target_version = api_destination.server_info().get('api_version', [3, 0, 0])
	print " Success"
except TransportError as e:
	print " ERROR:", e.message
	exit(1)
except:
	print " ERROR"
	print ""
	raise

print ""

print "fetching source templates"
source_templates = read_templates(api_source, source_version, options.include_restricted, options.templates)
print "  done"
for template in source_templates:
	print ""
	try:
		print "inserting template %s" % template.get('name', '[name unknown]')
		insert_template(api_destination, target_version, template, options.overwrite_on_conflict)
		print "  done"
	except:
		import traceback
		print traceback.print_exc()
		print "  ERROR"
