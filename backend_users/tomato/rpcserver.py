#!/usr/bin/python
# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import sys

import config
from . import api
from .lib import util, sslrpc2, logging #@UnresolvedImport
from .lib.error import Error, UserError, InternalError

import ssl

def logCall(function, args, kwargs):
	logging.log(category="api", method=function.__name__, args=args, kwargs=kwargs)

def handleError(error, function, args, kwargs):
	if not isinstance(error, Error):
		if isinstance(error, TypeError) and function.__name__ in str(error):
			error = UserError.wrap(error, data={"function": function.__name__, "args": args, "kwargs": kwargs})
		else:
			error = InternalError.wrap(error, data={"function": function.__name__, "args": args, "kwargs": kwargs})
	logging.logException()
	error.dump()
	return error

def runServer(server):
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass

global server

def start():
	global server
	print >>sys.stderr, "Starting RPC server..."
	def wrapError(error, method, args, kwargs):
		error = handleError(error, method, args, kwargs)
		return sslrpc2.Failure(error.raw)
	server = sslrpc2.Server(('0.0.0.0', config.SERVER_PORT), beforeExecute=logCall, onError=wrapError, keyfile=config.SERVER_CERT,
		certfile=config.SERVER_CERT, ca_certs=config.SERVER_CA_CERTS, cert_reqs=ssl.CERT_REQUIRED)
	server.registerContainer(api)
	util.start_thread(server.serve_forever)
	print >>sys.stderr, "done."

def stop():
	server.shutdown()