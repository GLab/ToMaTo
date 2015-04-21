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

import sys, threading
import django.db

import config
from . import currentUser, api, login, dump
from .lib import db, util, rpc, logging #@UnresolvedImport
from .lib.error import Error, UserError, InternalError

def logCall(function, args, kwargs):
	logging.log(category="api", method=function.__name__, args=args, kwargs=kwargs, user=currentUser().name if currentUser() else None)

class Wrapper:
	def __init__(self):
		self.semaphore = threading.Semaphore(config.MAX_REQUESTS)
	def __enter__(self):
		self.semaphore.acquire()
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.semaphore.release()
		if django.db.transaction.is_dirty():
			django.db.transaction.commit()
		django.db.connection.close()

@db.commit_after
def handleError(error, function, args, kwargs):
	if not isinstance(error, Error):
		if isinstance(error, TypeError) and function.__name__ in str(error):
			error = UserError.wrap(error, data={"function": function.__name__, "args": args, "kwargs": kwargs})
		else:
			error = InternalError.wrap(error, data={"function": function.__name__, "args": args, "kwargs": kwargs})
	logging.logException()
	if isinstance(error, InternalError):
		dump.dumpException()
	return error

@db.commit_after
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
	if isinstance(error, rpc.Fault):
		return error
	assert isinstance(error, Error)
	if error.code == UserError.NOT_LOGGED_IN:
		return rpc.xmlrpc.ErrorUnauthorized()
	return rpc.Fault(999, error.rawstr)

def start():
	print >>sys.stderr, "Starting RPC servers"
	global servers
	del servers[:]
	for settings in config.SERVER:
		server_address = ('', settings["PORT"])
		sslOpts = None
		if settings["SSL"]:
			sslOpts = rpc.SSLOpts(private_key=settings["SSL_OPTS"]["key_file"], certificate=settings["SSL_OPTS"]["cert_file"], client_certs=None)
		server = rpc.xmlrpc.XMLRPCServerIntrospection(server_address, sslOpts=sslOpts, loginFunc=login, wrapper=Wrapper(), beforeExecute=logCall, afterExecute=afterCall, onError=wrapError)
		server.register(api)
		print >>sys.stderr, " - %s:%d, SSL: %s" % (server_address[0], server_address[1], bool(sslOpts))
		util.start_thread(server.serve_forever)
		servers.append(server)

def stop():
	for server in servers:
		server.shutdown()