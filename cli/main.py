#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, xmlrpclib, getpass

if not len(sys.argv) == 2:
  print "ToMaTo control tool\nUsage: %s URL" % sys.argv[0]
  sys.exit(1)

url=sys.argv[1]
user=raw_input("Username: ")
password=getpass.getpass("Password: ")
api=xmlrpclib.ServerProxy('https://%s:%s@%s' % (user, password, url), allow_none=1)

def list():
  return api.system.listMethods()
  
def help(method):
  print "Signature: " + api.system.methodSignature(method)
  print api.system.methodHelp(method)

# Readline and tab completion support
import atexit
import readline
import rlcompleter
from traceback import print_exc

print 'Type "list()" or "help(method)" for more information.'

prompt = user

try:
  while True:
    command = ""
    while True:
      # Get line
      try:
        if command == "":
          sep = ">>> "
        else:
          sep = "... "
        line = raw_input(prompt + sep)
        # Ctrl-C
      except KeyboardInterrupt:
        command = ""
        print
        break

      # Build up multi-line command
      command += line

      # Blank line or first line does not end in :
      if line == "" or (command == line and line[-1] != ':'):
        break

      command += os.linesep

    # Blank line
    if command == "":
      continue
    # Quit
    elif command in ["q", "quit", "exit"]:
      break

    try:
      try:
        # Try evaluating as an expression and printing the result
        result = eval(command)
        if result is not None:
          print result
      except SyntaxError:
        # Fall back to executing as a statement
        exec command
    except xmlrpclib.ProtocolError, err:
      # Avaid revealing password in error url
      print "Protocol Error %s: %s" % (err.errcode, err.errmsg)
    except Exception, err:
      print_exc()

except EOFError:
  print
  pass