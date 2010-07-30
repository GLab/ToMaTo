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
		try:
			function = getattr(self.api,functionPath)
		except Fault, f:
			self._cbRender(f, request)
		else:
			request.setHeader("content-type", "text/xml")
			defer.maybeDeferred(function, *args, user=user).addErrback(self._ebRender).addCallback(self._cbRender,request)
			return server.NOT_DONE_YET

def run_server():
	api_server = APIServer(PublicAPI())
	reactor.listenTCP(8000, server.Site(api_server))
	reactor.run()
