# -*- coding: utf-8 -*-

import api
from ldapauth import LdapUser

import xmlrpclib
from twisted.web import xmlrpc, server, http
from twisted.internet import defer, reactor

class User():
	valid_users={}
	def __init__(self, user, password):
		self.username=user
		self.password=password
		ldap=LdapUser(user)
		self.is_valid=ldap.authenticate(password)
		if self.is_valid:
			self.is_user=ldap.is_user()
			self.is_admin=ldap.is_admin()

class APIServer(xmlrpc.XMLRPC):
	def __init__(self, papi):
		self.api=papi
		xmlrpc.XMLRPC.__init__(self)

	def authenticate(self, username, password):
		if User.valid_users.has_key(username):
			user=User.valid_users[username]
			if user.password==password:
				return user
		user=User(username, password)
		if user.is_valid:
			User.valid_users[username]=user
		return user

	def execute(self, function, args, user):
		try:
			return function(*args, user=user)
		except xmlrpclib.Fault, f:
			api.logger.log("Error: %s"%f, user=user.username)
			raise f
		#except Exception, exc:
		#	api.logger.log("Exception: %s" % exc, user=user.username)
		#	raise xmlrpclib.Fault(api.Fault.UNKNOWN, '%s:%s' % (exc.__class__.__name__, exc) )

	def render(self, request):
		username=request.getUser()
		passwd=request.getPassword()
		user=self.authenticate(username, passwd)
		if not user.is_valid:
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

def run_server():
	api_server=APIServer(api)
	reactor.listenTCP(8000, server.Site(api_server))
	reactor.run()

