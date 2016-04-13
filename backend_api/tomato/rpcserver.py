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

from . import api, login, getCurrentUserInfo
from .lib import util, rpc, logging, exceptionhandling  #@UnresolvedImport
from .lib.error import Error, UserError, InternalError
from lib.settings import settings

def logCall(function, args, kwargs):
	logging.log(category="api", method=function.__name__, args=args, kwargs=kwargs, user=getCurrentUserInfo().get_username() if getCurrentUserInfo() else None)

def handleError(error, function, args, kwargs):
	if not isinstance(error, Error):
		if isinstance(error, TypeError) and function.__name__ in str(error):
			error = UserError.wrap(error, data={"function": function.__name__, "args": args, "kwargs": kwargs})
		else:
			error = InternalError.wrap(error, data={"function": function.__name__, "args": args, "kwargs": kwargs})
	exceptionhandling.writedown_current_exception(exc=error)
	return error

def afterCall(*args, **kwargs):
	pass

def runServer(server):
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass

servers = []

def wrapError(error, func, args, kwargs):
	error = handleError(error, func, args, kwargs)
	assert isinstance(error, Error)
	import traceback
	error.data['trace'] = traceback.format_exc()
	if isinstance(error, InternalError):
		print >>sys.stderr, error
	if error.code == UserError.NOT_LOGGED_IN:
		return rpc.xmlrpc.ErrorUnauthorized()
	return rpc.Fault(999, error.rawstr)

def start():
	print >>sys.stderr, "Starting RPC servers"
	global servers
	del servers[:]
	for conf in settings.get_own_interface_config():
		server_address = ('', conf['port'])
		sslOpts = None
		if conf.get('ssl', False):
			sslOpts = rpc.SSLOpts(private_key=settings.get_ssl_key_filename(), certificate=settings.get_ssl_cert_filename(), client_certs=None)
		server = rpc.xmlrpc.XMLRPCServerIntrospection(server_address, sslOpts=sslOpts, loginFunc=login, beforeExecute=logCall, afterExecute=afterCall, onError=wrapError)
		server.register(api)
		print >>sys.stderr, " - %s:%d, SSL: %s" % (server_address[0], server_address[1], bool(sslOpts))
		util.start_thread(server.serve_forever)
		servers.append(server)

def stop():
	for server in servers:
		server.shutdown()