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

import xmlrpclib, traceback
from twisted.web import xmlrpc, server, http
from twisted.internet import defer, reactor, ssl

from tomato import fault

class Introspection():
	def __init__(self, papi):
		self.api=papi

	def listMethods(self, user=None): #@UnusedVariable, pylint: disable-msg=W0613
		return [m for m in dir(self.api) if (callable(getattr(self.api, m)) and not m.startswith("_"))]

	def methodSignature(self, method, user=None): #@UnusedVariable, pylint: disable-msg=W0613
		func = getattr(self.api, method)
		if not func:
			return "Unknown method: %s" % method
		import inspect
		argspec = inspect.getargspec(func)
		argstr = inspect.formatargspec(argspec.args[:-1], defaults=argspec.defaults[:-1])
		return method + argstr

	def methodHelp(self, method, user=None): #@UnusedVariable, pylint: disable-msg=W0613
		func = getattr(self.api, method)
		if not func:
			return "Unknown method: %s" % method
		doc = func.__doc__
		if not doc:
			return "No documentation for: %s" % method
		return doc
		
class APIServer(xmlrpc.XMLRPC):
	def __init__(self, papi, login):
		self.api=papi
		self.login=login
		self.introspection=Introspection(self.api)
		xmlrpc.XMLRPC.__init__(self, allowNone=True)
		self.logger = tomato.lib.log.Logger(tomato.config.log_dir + "/api.log")

	def log(self, function, args, user):
		if len(str(args)) < 50:
			self.logger.log("%s%s" %(function.__name__, args), user=user.name)
		else:
			self.logger.log(function.__name__, bigmessage=str(args)+"\n", user=user.name)

	def execute(self, function, args, user):
		try:
			self.log(function, args, user)
			return function(*(args[0]), user=user, **(args[1])) #pylint: disable-msg=W0142
		except xmlrpc.Fault, exc:
			fault.log(exc)
			raise
		except Exception, exc:
			fault.log(exc)
			self.logger.log("Exception: %s" % exc, user=user.name)
			raise fault.wrap(exc)

	def render(self, request):
		username=request.getUser()
		passwd=request.getPassword()
		user=self.login(username, passwd)
		if not user:
			request.setResponseCode(http.UNAUTHORIZED)
			if username=='' and passwd=='':
				return 'Authorization required!'
			else:
				return 'Authorization Failed!'
		request.content.seek(0, 0)
		args, functionPath=xmlrpclib.loads(request.content.read())
		function = None
		if hasattr(self.api, functionPath):
			function=getattr(self.api, functionPath)
		if functionPath.startswith("_"):
			functionPath = functionPath[1:]
		if hasattr(self.introspection, functionPath):
			function=getattr(self.introspection, functionPath)
		if function:
			request.setHeader("content-type", "text/xml")
			defer.maybeDeferred(self.execute, function, args, user).addErrback(self._ebRender).addCallback(self._cbRender, request)
			return server.NOT_DONE_YET

def run():
	api_server=APIServer(tomato.api, tomato.login)
	if tomato.config.server_ssl:
		sslContext = ssl.DefaultOpenSSLContextFactory(tomato.config.server_ssl_private_key, tomato.config.server_ssl_ca_key) 
		reactor.listenSSL(tomato.config.server_port, server.Site(api_server), contextFactory = sslContext) #@UndefinedVariable, pylint: disable-msg=E1101
	else:
		reactor.listenTCP(tomato.config.server_port, server.Site(api_server)) #@UndefinedVariable, pylint: disable-msg=E1101
	reactor.run() #@UndefinedVariable, pylint: disable-msg=E1101
	
if __name__ == "__main__":
	run()
