#!/usr/bin/python
# -*- coding: utf-8 -*-

import xmlrpclib, code, argparse, getpass, readline, rlcompleter, sys, os, imp, ssl, urlparse
from lib import getConnection, createUrl

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

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
	parser.add_argument("--url" , "-u", required=False, help="the whole URL of the server")
	parser.add_argument("--protocol" , required=False, default="http+xmlrpc", help="the protocol of the server")
	parser.add_argument("--hostname" , "-h", required=False, help="the host of the server")
	parser.add_argument("--port", "-p", default=8000, help="the port of the server")
	parser.add_argument("--ssl", "-s", action="store_true", default=False, help="whether to use ssl")
	parser.add_argument("--client_cert", "-c", required=False, default=None, help="path of the ssl certificate")
	parser.add_argument("--username", "-U", help="the username to use for login")
	parser.add_argument("--password", "-P", help="the password to use for login")
	parser.add_argument("--file", "-f", help="a file to execute")
	parser.add_argument("arguments", nargs="*", help="python code to execute directly")
	options = parser.parse_args()
	if not options.username and not options.client_cert:
		options.username=raw_input("Username: ")
	if not options.password and not options.client_cert:
		options.password=getpass.getpass("Password: ")
	if options.ssl and options.protocol == "http+xmlrpc":
		options.protocol = "https+xmlrpc"
	return options


def runInteractive(locals):
	"""
	Creates a interactive console based on the local available methods.

	Parameter *locals*:
		Dict containing a connection to an API, a help function and a file load function.
	"""
	prompt = "ToMaTo"
	readline.parse_and_bind("tab: complete")
	readline.set_completer(rlcompleter.Completer(locals).complete)
	console = code.InteractiveConsole(locals)
	console.interact('Type "help()" or "help(method)" for more information.')
	
def runSource(locals, source):
	"""
	Executes a python code using an interpreter based on the methods provided by the API found in locals.

	Parameter *locals*:
		Dict containing a connection to an API, a help function and a file load function.
	Parameter *source*:
		Source code to execute

	
	"""
	interpreter = code.InteractiveInterpreter(locals)
	interpreter.runsource(source)

def runFile(locals, file, options):
	"""
	Opens a connection to a remote socket at address (host, port) and closes it to open the TCP port.

	Parameter *locals*:
		Dict containing a connection to an API, a help function and a file load function.
	Parameter *file*:
		Path to the file which should be executed
	Parameter *options*:
		Command-line arguments which will be used to create an interactive console which executes the file.

	"""
	sys.path.insert(0, os.path.dirname(file))
	def shell():
		runInteractive(locals)
	locals["shell"] = shell
	if options.url:
		parsed = urlparse.urlparse(options.url)
		locals["__hostname__"] = parsed.hostname
	else:
		locals["__hostname__"] = options.hostname
	__builtins__.__dict__.update(locals)
	locals["__name__"]="__main__"
	locals["__file__"]=file
	execfile(file, locals)
	sys.path.pop(0)

def getLocals(api):
	"""
	Combines the api with additional functionalities in one dictionary. It adds a list of all commands, a help method and
	a method to load and initialize python modules from a file.

	Parameter *api*:
		Connection to a host api

	Return value:
		This method returns a dictionary with a connection to a API, an help method and a method to load and initialize python modules from a file.

	"""
	locals = {}
	def help(method=None):
		if method is None:
			print "Available methods:\tType help(method) for more infos."
			print ", ".join(api._listMethods())
		else:
			if not isinstance(method, str):
				method = filter(lambda name: locals[name] is method, locals)[0]
			print "Signature: " + api._methodSignature(method)
			print api._methodHelp(method)
	def load(file, name=None):
		files = filter(lambda dir: os.path.exists(os.path.join(dir, file)), sys.path)
		if files:
			file = os.path.join(files[0], file)
		if not name:
			name = os.path.basename(file)
		mod = imp.load_source(name, file)
		locals[name] = mod
		return mod
	locals.update(api=api, help=help, load=load)
	try:
		for func in api._listMethods():
			locals[func.replace(".", "_")] = getattr(api, func)
	except xmlrpclib.ProtocolError, err:
		print "Protocol Error %s: %s" % (err.errcode, err.errmsg)
		sys.exit(-1)
	except ssl.SSLError, exc:
		print "SSL error: %s" % exc.strerror
		sys.exit(-1)
	return locals

def run():
	"""
	Parses the command-line arguments, opens an API connection and creates access to the available commands of the host.
	It decides based on the options whether to directly execute python code or to execute a file or to grant access to the interactive cli.

	"""
	options = parseArgs()
	url = options.url if options.url else createUrl(options.protocol, options.hostname, options.port, options.username, options.password)
	api = getConnection(url, options.client_cert)
	locals = getLocals(api)
	if options.arguments:
		runSource(locals, "\n".join(options.arguments))
	elif options.file:
		runFile(locals, options.file, options)
	else:
		runInteractive(locals)
	
if __name__ == "__main__":
	run()