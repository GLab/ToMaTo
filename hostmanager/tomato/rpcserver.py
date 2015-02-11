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

from . import config, login, api, handleError as handleCurrentError
from . import currentUser
from .lib import db, rpc, logging  # @UnresolvedImport
from .lib.error import Error, InternalError


def logCall(function, args, kwargs):
	logging.log(category="api", method=function.__name__, args=args, kwargs=kwargs, user=currentUser().name)

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
		error = InternalError.wrap(error)
	if isinstance(error, InternalError):
		handleCurrentError()
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


def start():
	print >> sys.stderr, "Starting RPC servers"
	for settings in config.SERVER:
		server_address = ('', settings["PORT"])
		sslOpts = rpc.SSLOpts(private_key=settings["SSL_OPTS"]["key_file"],
							  certificate=settings["SSL_OPTS"]["cert_file"],
							  client_certs=settings["SSL_OPTS"]["client_certs"])
		server = rpc.runServer(type=settings.get("TYPE", "https+xmlrpc"), address=server_address, sslOpts=sslOpts,
							   certCheck=login, wrapper=Wrapper(), beforeExecute=logCall, afterExecute=afterCall,
								onError=handleError, api=api)
		print >> sys.stderr, " - %s %s:%d" % (
		settings.get("TYPE", "https+xmlrpc"), server_address[0], server_address[1])
		servers.append(server)


def stop():
	for server in servers:
		server.shutdown()