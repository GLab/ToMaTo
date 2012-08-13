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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.	If not, see <http://www.gnu.org/licenses/>

import xmlrpclib, socket, SocketServer, BaseHTTPServer, collections
from OpenSSL import SSL

#Bugfix: Python 2.6 will not call the needed shutdown_request function
if not hasattr(SocketServer.BaseServer, "shutdown_request"):
	def _handle_request_noblock(self):
		try:
			request, client_address = self.get_request()
		except socket.error:
			return
		if self.verify_request(request, client_address):
			try:
				self.process_request(request, client_address)
			except:
				self.handle_error(request, client_address)
				self.shutdown_request(request)
	SocketServer.BaseServer._handle_request_noblock = _handle_request_noblock
	def process_request(self, request, client_address):
		self.finish_request(request, client_address)
		self.shutdown_request(request)
	SocketServer.BaseServer.process_request = process_request


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
			#explicitly shutdown.	socket.close() merely releases
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
		if not self.server.checkAuth(username, password):
			self.send_error(401)
			return self.finish()
		(method, args, kwargs) = self.getRpcRequest()
		func = self.server.findMethod(method)
		try:
			ret = self.server.execute(func, args, kwargs)
			self.send((ret,))
		except Exception, err:
			if not isinstance(err, xmlrpclib.Fault):
				err = xmlrpclib.Fault(-1, str(err))
			self.send(err)
	def log_message(self, format, *args):
		pass
	def send(self, response):
		res = xmlrpclib.dumps(response, methodresponse=True, allow_none=True)
		self.send_response(200)
		self.send_header("Content-Type", "text/xml")
		self.end_headers()
		self.wfile.write(res)
		self.finish()
	def getRpcRequest(self):
		length = int(self.headers.get("Content-Length", None))
		args, method = xmlrpclib.loads(self.rfile.read(length))
		kwargs = {}
		if len(args) == 2 and isinstance(args[0], list) and isinstance(args[1], dict):
			(args, kwargs) = (args[0], args[1])
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
	def __init__(self, address, loginFunc=lambda u, p: True, sslOpts=False, beforeExecute=None, afterExecute=None, onError=None):
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
	def execute(self, func, args, kwargs):
		try:
			if callable(self.beforeExecute):
				self.beforeExecute(func, args, kwargs)
			res = func(*args, **kwargs)
			if callable(self.afterExecute):
				self.afterExecute(func, args, kwargs, res)
			return res
		except Exception, exc:
			if callable(self.onError):
				res = self.onError(exc, func, args, kwargs)
				if res:
					exc = res
			raise exc
	def findMethod(self, method):
		return self.functions.get(method, None)
	def checkAuth(self, username, password):
		if username:
			return self.loginFunc(username, password)
		return False


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


class ServerProxy(object):
	def __init__(self, url, **kwargs):
		self._xmlrpc_server_proxy = xmlrpclib.ServerProxy(url, **kwargs)
	def __getattr__(self, name):
		call_proxy = getattr(self._xmlrpc_server_proxy, name)
		def _call(*args, **kwargs):
			return call_proxy(args, kwargs)
		return _call