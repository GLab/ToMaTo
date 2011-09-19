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

import tomato.lib.log

import xmlrpclib, socket, SocketServer, BaseHTTPServer, collections, time, sys
from OpenSSL import SSL

from tomato import fault
from tomato.lib import db, util

class SecureRequestHandler:
	def setup(self):
		self.connection = self.request
		if self.server.sslOpts:
			self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
			self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
		else:
			self.rfile = self.connection.makefile('rb', self.rbufsize)
			self.wfile = self.connection.makefile('wb', self.wbufsize)	

SSLOpts = collections.namedtuple("SSLOpts", ["private_key", "certificate"])

class SecureServer():
	def __init__(self, sslOpts):
		self.sslOpts = sslOpts
		if sslOpts:
			ctx = SSL.Context(SSL.SSLv23_METHOD)
			ctx.use_privatekey_file(sslOpts.private_key)
			ctx.use_certificate_file(sslOpts.certificate)
			self.plainSocket = self.socket
			self.socket = SSL.Connection(ctx, self.plainSocket)
			self.server_bind()
			self.server_activate()
	def shutdown_request(self, request):
		"""Called to shutdown and close an individual request."""
		try:
			#explicitly shutdown.  socket.close() merely releases
			#the socket and waits for GC to perform the actual close.
			if self.sslOpts:
				request.shutdown()
			else:
				request.shutdown(socket.SHUT_WR)
		except socket.error:
			pass #some platforms may raise ENOTCONN here
		self.close_request(request)
				
class XMLRPCHandler(SecureRequestHandler, BaseHTTPServer.BaseHTTPRequestHandler):
	def do_POST(self):
		(username, password) = self.getCredentials()
		user = self.server.getAuth(username, password)
		if not user:
			self.send_error(401)
			return self.finish()
		(method, args, kwargs) = self.getRpcRequest()
		func = self.server.findMethod(method)
		try:
			ret = self.server.execute(func, args, kwargs, user)
			self.send((ret,), method)
		except Exception, err:
			if not isinstance(err, xmlrpclib.Fault):
				err = xmlrpclib.Fault(-1, str(err))
			self.send(err, method)
	def log_message(self, format, *args):
		pass
	def send(self, response, methodName=None):
		res = xmlrpclib.dumps(response, methodname=methodName, methodresponse=True, allow_none=True)
		self.send_response(200)
		self.send_header("Content-Type", "text/xml")
		self.end_headers()
		self.wfile.write(res)
		self.finish()
	def getRpcRequest(self):
		length = int(self.headers.get("Content-Length", None))
		(args, kwargs), method = xmlrpclib.loads(self.rfile.read(length))
		return (method, args, kwargs)
	def getCredentials(self):
		authstr = self.headers.get("Authorization", None)
		if not authstr:
			return (None, None)
		(authmeth, auth) = authstr.split(' ',1)
		if 'basic' != authmeth.lower():
			return (None, None)
		auth = auth.strip().decode('base64')
		username, password = auth.split(':',1)
		return (username, password)

class XMLRPCServer(SecureServer, SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	def __init__(self, address, loginFunc, sslOpts=False, beforeExecute=None, afterExecute=None, onError=None):
		BaseHTTPServer.HTTPServer.__init__(self, address, XMLRPCHandler, bind_and_activate=not bool(sslOpts))
		SecureServer.__init__(self, sslOpts)
		self.functions = {}
		self.loginFunc = loginFunc
		self.beforeExecute = beforeExecute
		self.afterExecute = afterExecute
		self.onError = onError
	def register(self, func, name=None):
		if not callable(func):
			for n in dir(func):
				fn = getattr(func, n)
				if callable(fn):
					self.register(fn)
		else:
			if not name:
				name = func.__name__
			self.functions[name] = func
	def execute(self, func, args, kwargs, user):
		try:
			if callable(self.beforeExecute):
				self.beforeExecute(func, args, kwargs, user)
			res = func(*args, user=user, **kwargs)
			if callable(self.afterExecute):
				self.afterExecute(func, args, kwargs, user, res)
			return res
		except Exception, exc:
			if callable(self.onError):
				res = self.onError(exc, func, args, kwargs, user)
				if res:
					exc = res
			raise exc
	def findMethod(self, method):
		return self.functions.get(method, None)
	def getAuth(self, username, password):
		user = None
		if username:
			user = self.loginFunc(username, password)
		return user

class XMLRPCServerIntrospection(XMLRPCServer):
	def __init__(self, *args, **kwargs):
		XMLRPCServer.__init__(self, *args, **kwargs)
		self.register(self.listMethods, "_listMethods")
		self.register(self.methodSignature, "_methodSignature")
		self.register(self.methodHelp, "_methodHelp")
		self.register(self.listMethods, "system.listMethods")
		self.register(self.methodSignature, "system.methodSignature")
		self.register(self.methodHelp, "system.methodHelp")

	def listMethods(self, user=None): #@UnusedVariable, pylint: disable-msg=W0613
		return filter(lambda name: not name.startswith("_"), self.functions.keys())
	
	def methodSignature(self, method, user=None): #@UnusedVariable, pylint: disable-msg=W0613
		func = self.findMethod(method)
		if not func:
			return "Unknown method: %s" % method
		import inspect
		argspec = inspect.getargspec(func)
		argstr = inspect.formatargspec(argspec.args[:-1], defaults=argspec.defaults[:-1])
		return method + argstr

	def methodHelp(self, method, user=None): #@UnusedVariable, pylint: disable-msg=W0613
		func = self.findMethod(method)
		if not func:
			return "Unknown method: %s" % method
		doc = func.__doc__
		if not doc:
			return "No documentation for: %s" % method
		return doc

logger = tomato.lib.log.Logger(tomato.config.LOG_DIR + "/api.log")

def logCall(function, args, kwargs, user):
	if len(str(args)) < 50:
		logger.log("%s%s" %(function.__name__, args), user=user.name)
	else:
		logger.log(function.__name__, bigmessage=str(args)+"\n", user=user.name)

@db.commit_after
def handleError(error, function, args, kwargs, user):
	if isinstance(error, xmlrpclib.Fault):
		fault.log(error)
	else:
		if not (isinstance(error, TypeError) and function.__name__ in str(error)):
			# not a wrong API call
			fault.log(error)
			logger.log("Exception: %s" % error, user=user.name)
		return fault.wrap(error)

@db.commit_after
def afterCall(*args, **kwargs):
	pass

def runServer(server):
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass

def run():
	servers = []
	print >>sys.stderr, "Starting RPC servers"
	for settings in tomato.config.SERVER:
		server_address = ('', settings["PORT"])
		sslOpts = None
		if settings["SSL"]:
			sslOpts = SSLOpts(private_key=settings["SSL_OPTS"]["private_key"], certificate=settings["SSL_OPTS"]["ca_key"])
		server = XMLRPCServerIntrospection(server_address, sslOpts=sslOpts, loginFunc=tomato.login, beforeExecute=logCall, onError=handleError)
		server.register(tomato.api)
		print >>sys.stderr, " - %s:%d, SSL: %s" % (server_address[0], server_address[1], bool(sslOpts))
		util.start_thread(server.serve_forever)
	try:
		while True:
			time.sleep(60)
	except KeyboardInterrupt:
		for server in servers:
			server.shutdown()
		
if __name__ == "__main__":
	run()
