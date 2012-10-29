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

import xmlrpclib, sys, traceback

import config
from . import fault, currentUser, api, login
from lib import db, util, rpc, logging #@UnresolvedImport


def logCall(function, args, kwargs):
	logging.log(category="api", method=function.__name__, args=args, kwargs=kwargs, user=currentUser().name)

@db.commit_after
def handleError(error, function, args, kwargs):
	if isinstance(error, xmlrpclib.Fault):
		fault.errors_add(error, traceback.format_exc())
	else:
		if not (isinstance(error, TypeError) and function.__name__ in str(error)):
			# not a wrong API call
			fault.errors_add(error, traceback.format_exc())
		logging.logException()
		return fault.wrap(error)

@db.commit_after
def afterCall(*args, **kwargs):
	pass

def runServer(server):
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass

servers = []

def start():
	print >>sys.stderr, "Starting RPC servers"
	global servers
	del servers[:]
	for settings in config.SERVER:
		server_address = ('', settings["PORT"])
		sslOpts = None
		if settings["SSL"]:
			sslOpts = rpc.SSLOpts(private_key=settings["SSL_OPTS"]["key_file"], certificate=settings["SSL_OPTS"]["cert_file"], client_certs=None)
		server = rpc.XMLRPCServerIntrospection(server_address, sslOpts=sslOpts, loginFunc=login, beforeExecute=logCall, afterExecute=afterCall, onError=handleError)
		server.register(api)
		print >>sys.stderr, " - %s:%d, SSL: %s" % (server_address[0], server_address[1], bool(sslOpts))
		util.start_thread(server.serve_forever)
		servers.append(server)
		
def stop():
	for server in servers:
		server.shutdown()