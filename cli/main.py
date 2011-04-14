#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, xmlrpclib, getpass, getopt, os

class options:
	ssl = False
	hostname = None
	port = 8000
	username = None
	file = None
	call = None
	password = None

optlist, args = getopt.getopt(sys.argv[1:], 'h:p:su:f:c:', ['hostname=', 'port=', 'ssl', 'username=', 'file=', 'call='])

for (opt, val) in optlist:
	if opt == "-h" or opt == "--hostname":
		options.hostname = val
	elif opt == "-p" or opt == "--port":
		options.port = int(val)
	elif opt == "-s" or opt == "--ssl":
		options.ssl = True
	elif opt == "-u" or opt == "--username":
		options.username = val
	elif opt == "-f" or opt == "--file":
		options.file = val
	elif opt == "-c" or opt == "--call":
		options.call = val

if not options.hostname:
	print "No hostname given"
	sys.exit(1)

if not options.username:
	options.username=raw_input("Username: ")
	
if not options.password:
	options.password=getpass.getpass("Password: ")
	
class ServerProxy(object):
    def __init__(self, url, **kwargs):
        self._xmlrpc_server_proxy = xmlrpclib.ServerProxy(url, **kwargs)
    def __getattr__(self, name):
        call_proxy = getattr(self._xmlrpc_server_proxy, name)
        def _call(*args, **kwargs):
            return call_proxy(args, kwargs)
        return _call
	
api=ServerProxy('%s://%s:%s@%s:%s' % ('https' if options.ssl else 'http', options.username, options.password, options.hostname, options.port), allow_none=True)

# Readline and tab completion support
import atexit
import readline
import rlcompleter
from traceback import print_exc

def get_name(instance):
	for name in globals:
		if globals[name] is instance:
			return name

def help(method=None):
	if method is None:
		print "Available methods:\tType help(method) for more infos."
		print ", ".join(api._listMethods())
	else:
		if type(method) != type('str'):
			method = get_name(method)
		print "Signature: " + api._methodSignature(method)
		print api._methodHelp(method)

globals = {"help": help}
try:
	for func in api._listMethods():
		globals[func] = getattr(api, func)
except xmlrpclib.ProtocolError, err:
	print "Protocol Error %s: %s" % (err.errcode, err.errmsg)
	sys.exit(-1)


def read_command_keyboard(prompt):
	command = ""
	while True:
		try:
			sep = "> " if command == "" else "~ "
			line = raw_input(prompt + sep)
		except KeyboardInterrupt:
			print ""
			return "q"
		command += line
		if line == "" or (command == line and line[-1] != ':'):
			break
		command += os.linesep
	return command 

def read_command_fd(fd):
	command = ""
	while True:
		line = fd.readline()
		if line == "":
			if command == "":
				raise EOFError
			else:
				return command
		else:
			line = line[:-1]
		command += line
		if line == "" or (command == line and line[-1] != ':'):
			break
		command += os.linesep
	return command

def exec_command(command):
	# Blank line
	if command == "":
		return
	# Quit
	elif command in ["q", "quit", "exit"]:
		sys.exit(0)

	try:
		try:
			# Try evaluating as an expression and printing the result
			result = eval(command, globals)
			if result is not None:
				print result
		except SyntaxError:
			# Fall back to executing as a statement
			exec command in globals
		except xmlrpclib.ProtocolError, err:
			# Avoid revealing password in error url
			print "Protocol Error %s: %s" % (err.errcode, err.errmsg)
		except xmlrpclib.Fault, f:
			print f
	except Exception, err:
		print_exc()

def run_interactive():
	print 'Type "help()" or "help(method)" for more information.'
	prompt = "ToMaTo"
	readline.parse_and_bind("tab: complete")
	readline.set_completer(rlcompleter.Completer(globals).complete)
	try:
		while True:
			exec_command(read_command_keyboard(prompt))
	except EOFError:
		print
	
def run_file(file):
	fd = open(file, "r")
	try:
		while True:
			exec_command(read_command_fd(fd))
	except EOFError:
		print
		
if options.call:
	exec_command(options.call)
elif options.file:
	run_file(options.file)
else:
	run_interactive()