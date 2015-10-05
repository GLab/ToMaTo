#!/usr/bin/python

from lib import getConnection, createUrl
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

	parser.add_argument("--include_restricted", default=False, help="whether to include restricted templates")
	parser.add_argument("--templates", "-t", metavar='T', nargs="+", default=None, help="only migrate templates with this name")
	parser.add_argument("--overwrite_on_conflict", default=False, action="store_true", help="in case of conflict, overwrite the template (default: ignore)")

	parser.add_argument("arguments", nargs="*", help="python code to execute directly")
	options = parser.parse_args()

	if not options.username_source and not options.client_cert_source:
		options.username_source=raw_input("Username for %s: " % options.hostname_source)
	if not options.password_source and not options.client_cert_source:
		options.password_source= getpass.getpass("Password for %s: " % options.hostname_source)
	if options.ssl_source and options.protocol_source == "http+xmlrpc":
		options.protocol_source = "https+xmlrpc"

	if not options.username_destination and not options.client_cert_destination:
		options.username_destination=raw_input("Username for %s: " % options.hostname_destination)
	if not options.password_destination and not options.client_cert_destination:
		options.password_destination= getpass.getpass("Password for %s: " % options.hostname_destination)
	if options.ssl_destination and options.protocol_destination == "http+xmlrpc":
		options.protocol_destination = "https+xmlrpc"

	return options



def _read_templates_3_0_0(api, include_restricted, template_names):
	results = []
	templates = api.resource_list('template')
	for t in templates:
		if include_restricted or not t['attrs'].get('restricted', False):
			if template_names is None or t['attrs']['name'] in template_names:
				templ = api.resource_info(t['id'], include_torrent_data=True)
				res_entry = {
					'name': templ['attrs']['name'],
					'tech': templ['attrs']['tech'],
					'attrs': {k: v for k, v in templ['attrs'].iteritems()
									 if k not in ['name', 'tech', 'torrent_data', 'torrent_data_hash', 'ready']},
					'torrent_data': templ['attrs']['torrent_data']
				}

				if 'creation_date' in res_entry['attrs']:
					res_entry['attrs']['creation_date'] = time.mktime(datetime.datetime.strptime(res_entry['attrs']['creation_date'], "%Y-%m-%d").timetuple())

				results.append(res_entry)

	return results


def _read_templates_4_0_0(api, include_restricted, template_names):
	results = []
	templates = api.template_list()
	for t in templates:
		if include_restricted or not t.get('restricted', False):
			if template_names is None or t['name'] in template_names:
				templ = api.resource_info(t['id'])
				res_entry = {
					'name': templ['name'],
					'tech': templ['tech'],
					'torrent_data': templ['torrent_data'],
					'attrs': {k: v for k, v in templ.iteritems()
									  if k not in ['name', 'tech', 'torrent_data', 'torrent_data_hash', 'ready']}
				}
				results.append(res_entry)
	return results

def _insert_template_3_0_0(api, template, overwrite_on_conflict):
	try:
		t = api.resource_create('template', {
			'tech': template['tech'],
			'name': template['name'],
			'torrent_data': template['torrent_data']
		})
		templ_id = t['id']
	except Exception, e:
		if not overwrite_on_conflict:
			raise e
		try:
			templates = api.resource_list['template']
			for t in templates:
				if t['attrs']['name'] == template['name'] and t['attrs']['tech'] == template['tech']:
					templ_id  = t['id']
		except:
			raise e
	try:
		api.resource_modify(templ_id, template['attrs'])
	except:
		for k, v in template['attrs'].iteritems():
			try:
				api.template_modify(templ_id, {k: v})
			except:
				print "  error setting %s=%s" % (k, v)


def _insert_template_4_0_0(api, template, overwrite_on_conflict):
	try:
		t = api.template_create(template['tech'], template['name'], {'torrent_data': template['torrent_data']})
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
	try:
		api.template_modify(templ_id, template['attrs'])
	except:
		for k, v in template['attrs'].iteritems():
			try:
				api.template_modify(templ_id, {k: v})
			except:
				print "  error setting %s=%s" % (k, v)



def read_templates(api, version, include_restricted, template_names):
	if version[0] == 3:
		return _read_templates_3_0_0(api, include_restricted, template_names)
	elif version[0] == 4:
		return _read_templates_4_0_0(api, include_restricted, template_names)
	else:
		print "unsupported source version: %s" % ".".join(version)

def insert_template(api, version, template, overwrite_on_conflict):
	if version[0] == 3:
		return _insert_template_3_0_0(api, template, overwrite_on_conflict)
	elif version[0] == 4:
		return _insert_template_4_0_0(api, template, overwrite_on_conflict)
	else:
		print "unsupported destination version: %s" % ".".join(version)




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
