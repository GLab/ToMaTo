# -*- coding: utf-8 -*-

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from base64 import b64decode

from util import *
from api import *
from ldapauth import *

import xmlrpclib
from twisted.web import xmlrpc, server, http
from twisted.internet import defer, protocol, reactor


Fault = xmlrpclib.Fault

class APIServer(xmlrpc.XMLRPC):
	def __init__(self, api):
		self.api = api
		xmlrpc.XMLRPC.__init__(self)
        
        def authenticate(self, user, passwd):
		return LdapUser(user).authenticate(passwd) 
        
	def render(self, request):
		user = request.getUser()
		passwd = request.getPassword()
		if not self.authenticate(user, passwd):
			request.setResponseCode(http.UNAUTHORIZED)
			if user=='' and passwd=='':
				return 'Authorization required!'
			else:
				return 'Authorization Failed!'
		request.content.seek(0, 0)
		args, functionPath = xmlrpclib.loads(request.content.read())
		try:
			function = getattr(self.api,functionPath)
		except Fault, f:
			self._cbRender(f, request)
		else:
			request.setHeader("content-type", "text/xml")
			defer.maybeDeferred(function, *args, username=user).addErrback(self._ebRender).addCallback(self._cbRender,request)
			return server.NOT_DONE_YET

def run_server():
	api_server = APIServer(PublicAPI())
	reactor.listenTCP(8000, server.Site(api_server))
	reactor.run()
