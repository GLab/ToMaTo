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

class User():
	valid_users={}
	def __init__(self,user,password):
		self.username=user
		self.password=password
		ldap=LdapUser(user)
		self.is_valid=ldap.authenticate(password)
		if self.is_valid:
			self.id_user=ldap.is_user()
			self.id_admin=ldap.is_admin()

class APIServer(xmlrpc.XMLRPC):
	def __init__(self, api):
		self.api = api
		xmlrpc.XMLRPC.__init__(self)
        
        def authenticate(self, username, password):
		if User.valid_users.has_key(username):
			user = User.valid_users[username]
			if user.password == password:
				return user
		user = User(username, password)
		if user.is_valid:
			User.valid_users[username]=user
		return user
        
        def execute(self, function, args, user):
		try:
			function(args, user=user)
		except Exception, exc:
			raise xmlrpclib.Fault(-1, '%s:%s' % (exc.__class__.__name__, exc) )
        
	def render(self, request):
		username = request.getUser()
		passwd = request.getPassword()
		user = self.authenticate(username, passwd)
		if not user.is_valid:
			request.setResponseCode(http.UNAUTHORIZED)
			if username=='' and passwd=='':
				return 'Authorization required!'
			else:
				return 'Authorization Failed!'
		request.content.seek(0, 0)
		args, functionPath = xmlrpclib.loads(request.content.read())
		if hasattr(self.api,functionPath):
			function = getattr(self.api,functionPath)
			request.setHeader("content-type", "text/xml")
			defer.maybeDeferred(self.execute, function, *args, user=user).addErrback(self._ebRender).addCallback(self._cbRender,request)
			return server.NOT_DONE_YET
		
def run_server():
	api_server = APIServer(PublicAPI())
	reactor.listenTCP(8000, server.Site(api_server))
	reactor.run()
