#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Requires python-ldap, python-twisted-web
"""

import glabnetman

import xmlrpclib
from twisted.web import xmlrpc, server, http
from twisted.internet import defer, reactor

class APIServer(xmlrpc.XMLRPC):
	def __init__(self, papi):
		self.api=papi
		xmlrpc.XMLRPC.__init__(self)

	def execute(self, function, args, user):
		try:
			return function(*args, user=user)
		except xmlrpclib.Fault, f:
			self.api.logger.log("Error: %s"%f, user=user.name)
			raise f
		#except Exception, exc:
		#	api.logger.log("Exception: %s" % exc, user=user.username)
		#	raise xmlrpclib.Fault(api.Fault.UNKNOWN, '%s:%s' % (exc.__class__.__name__, exc) )

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
	reactor.listenTCP(8000, server.Site(api_server))
	reactor.run()

