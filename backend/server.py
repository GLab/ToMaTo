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

"""
Requires python-ldap, python-twisted-web
"""

import glabnetman

import xmlrpclib, traceback
from twisted.web import xmlrpc, server, http
from twisted.internet import defer, reactor, ssl

class APIServer(xmlrpc.XMLRPC):
	def __init__(self, papi):
		self.api=papi
		xmlrpc.XMLRPC.__init__(self)
		self.logger = glabnetman.log.Logger(glabnetman.config.log_dir + "/api.log")

	def log(self, function, args, user):
		if len(str(args)) < 50:
			self.logger.log("%s%s" %(function.__name__, args), user=user.name)
		else:
			self.logger.log(function.__name__, bigmessage=str(args), user=user.name)

	def execute(self, function, args, user):
		try:
			self.log(function, args, user)
			return function(*args, user=user)
		except xmlrpc.Fault:
			raise
		except Exception, exc:
			traceback.print_exc()
			glabnetman.fault.errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc())
			self.logger.log("Exception: %s" % exc, user=user.name)
			raise glabnetman.fault.new(glabnetman.fault.UNKNOWN, '%s:%s' % (exc.__class__.__name__, exc) )

	def render(self, request):
		username=request.getUser()
		passwd=request.getPassword()
		user=self.api.login(username, passwd)
		if not user:
			request.setResponseCode(http.UNAUTHORIZED)
			if username=='' and passwd=='':
				return 'Authorization required!'
			else:
				return 'Authorization Failed!'
		request.content.seek(0, 0)
		args, functionPath=xmlrpclib.loads(request.content.read())
		if hasattr(self.api, functionPath):
			function=getattr(self.api, functionPath)
			request.setHeader("content-type", "text/xml")
			defer.maybeDeferred(self.execute, function, args, user).addErrback(self._ebRender).addCallback(self._cbRender, request)
			return server.NOT_DONE_YET

if __name__ == "__main__":
	api_server=APIServer(glabnetman)
	if glabnetman.config.server_ssl:
		sslContext = ssl.DefaultOpenSSLContextFactory(glabnetman.config.server_ssl_private_key, glabnetman.config.server_ssl_ca_key) 
		reactor.listenSSL(glabnetman.config.server_port, server.Site(api_server), contextFactory = sslContext)
	else:
		reactor.listenTCP(glabnetman.config.server_port, server.Site(api_server))
	reactor.run()