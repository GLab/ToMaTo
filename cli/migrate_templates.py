__author__ = 't-gerhard'

from .lib import getConnection, createUrl

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

	parser.add_argument("--url_source" , "-su", required=False, help="the whole URL of the server")
	parser.add_argument("--protocol_source", required=False, default="http+xmlrpc", help="the protocol of the server")
	parser.add_argument("--hostname_source", "-sh", required=False, help="the host of the server")
	parser.add_argument("--port_source", "-sp", default=8000, help="the port of the server")
	parser.add_argument("--ssl_source", "-ss", action="store_true", default=False, help="whether to use ssl")
	parser.add_argument("--client_cert_source", "-sc", required=False, default=None, help="path of the ssl certificate")
	parser.add_argument("--username_source", "-sU", help="the username to use for login")
	parser.add_argument("--password_source", "-sP", help="the password to use for login")

	parser.add_argument("--url_destination" , "-du", required=False, help="the whole URL of the server")
	parser.add_argument("--protocol_destination", required=False, default="http+xmlrpc", help="the protocol of the server")
	parser.add_argument("--hostname_destination", "-dh", required=False, help="the host of the server")
	parser.add_argument("--port_destination", "-dp", default=8000, help="the port of the server")
	parser.add_argument("--ssl_destination", "-ds", action="store_true", default=False, help="whether to use ssl")
	parser.add_argument("--client_cert_destination", "-dc", required=False, default=None, help="path of the ssl certificate")
	parser.add_argument("--username_destination", "-dU", help="the username to use for login")
	parser.add_argument("--password_destination", "-dP", help="the password to use for login")

	parser.add_argument("arguments", nargs="*", help="python code to execute directly")
	options = parser.parse_args()
	if not options.username and not options.client_cert:
		options.username=raw_input("Username: ")
	if not options.password and not options.client_cert:
		options.password=getpass.getpass("Password: ")
	if options.ssl and options.protocol == "http+xmlrpc":
		options.protocol = "https+xmlrpc"
	return options



def _read_templates_3_0_0(api):
	templates = api.resource_list('template')
	for t in templates:
		pass  # todo: transform to internal format.

def _read_templates_4_0_0(api):
	pass  # todo: read them and transform to internal format.

def _insert_template_3_0_0(api, template):
	pass  # todo: takes internal formatted template and inserts it to api

def _insert_template_4_0_0(api, template):
	pass  # todo: takes internal formatted template and inserts it to api



def read_templates(api, version):
	if version[0] == 3:
		return _read_templates_3_0_0(api)
	elif version[0] == 4:
		return _read_templates_4_0_0(api)
	else:
		print "unknown source version: %s" % ".".join(version)

def insert_template(api, version, template):
	if version[0] == 3:
		return _insert_template_3_0_0(api, template)
	elif version[0] == 4:
		return _insert_template_4_0_0(api, template)
	else:
		print "unknown source version: %s" % ".".join(version)




options = parseArgs()

print "logging in to source backend..."
if options.url_source:
	url_source = options.url_source
else:
	url_source = createUrl(options.protocol_source, options.hostname_source, options.port_source, options.username_source, options.password_source)
api_source = getConnection(url_source, options.client_cert_source)

print "logging in to destination backend..."
if options.url_destination:
	url_destination = options.url_destination
else:
	url_destination = createUrl(options.protocol_destination, options.hostname_destination, options.port_destination, options.username_destination, options.password_destination)
api_destination = getConnection(url_destination, options.client_cert_destination)

source_version = api_source.server_info().get('api_version', (3, 0, 0))
target_version = api_destination.server_info().get('api_version', (3, 0, 0))

source_templates = read_templates(api_source, source_version)
for template in source_templates:
	try:
		print "inserting template %s" % template.get('name', '[name unknown]')
		insert_template(api_destination, target_version, template)
		print "  done"
	except:
		print "  ERROR"
