# -*- coding: utf-8 -*-

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

from api import *

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
	rpc_paths = ('/RPC2',)

def run_server():
	server = SimpleXMLRPCServer(("localhost", 8000), requestHandler=RequestHandler)
	server.register_introspection_functions()
	server.register_instance(PublicAPI())
	server.serve_forever()