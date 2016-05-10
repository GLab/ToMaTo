#!/usr/bin/python

# this script can execute tests.
# assumption: the API can be reached at localhost:8000 with user admin:changeme

import sys
import unittest
import json

TOMATO_BACKEND_API_MODULE = "backend_api"
TOMATO_MODULES = ("backend_api", "backend_accounting", "backend_core", "backend_debug", "backend_users")

sys.path.insert(1, "../cli/")
import lib as tomato
from lib.error import UserError
from lib.userflags import flags as userflags


class InternalMethodProxy(object):
	"""
	a method that will be proxied to the backend_api's debug_run_internal_api_call methdod
	"""
	__slots__ = ("_backend_api", "_tomato_module", "_methodname")

	def __init__(self, backend_api, tomato_module, methodname):
		self._backend_api = backend_api
		self._tomato_module = tomato_module
		self._methodname = methodname

	def __call__(self, *args, **kwargs):
		return self._backend_api.debug_run_internal_api_call(self._tomato_module, self._methodname, *args, **kwargs)


class InternalAPIProxy(object):
	"""
	a server proxy which uses backend_api's debug_run_internal_api_call to send commands to certain tomato modules
	"""
	__slots__ = ("_backend_api", "_tomato_module")

	def __init__(self, backend_api, tomato_module):
		self._backend_api = backend_api
		self._tomato_module = tomato_module

	def __getattr__(self, item):
		return InternalMethodProxy(self._backend_api, self._tomato_module, item)




class ProxyHolder(object):
	"""
	a class which has for each backend_* module an attribute holding a proxy which can execute API commands
	  on the respective module.
	"""
	__slots__ = ("backend_api", "backend_core", "backend_debug", "backend_users", "backend_accounting",
	             "username", "password")

	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.backend_api = tomato.getConnection(tomato.createUrl("http+xmlrpc", "localhost", 8000, self.username, self.password))
		for module in TOMATO_MODULES:
			if module != TOMATO_BACKEND_API_MODULE:
				setattr(self, module, InternalAPIProxy(self.backend_api, module))


proxy_holder = ProxyHolder("admin", "changeme")
with open("testhosts.json") as f:
	test_hosts = json.load(f)
class ProxyHoldingTestCase(unittest.TestCase):
	"""
	:type proxy_holder: ProxyHolder
	:type test_host_addresses: list(str)
	"""

	def __init__(self, methodName='runTest'):
		super(ProxyHoldingTestCase, self).__init__(methodName)
		self.proxy_holder = proxy_holder
		self.test_host_addresses = test_hosts
		self.host_site_name = "testhosts"
		self.default_organization_name = "others"
		self.default_user_name = "admin"

	def assertRaisesError(self, excClass, errorCode, callableObj=None, *args, **kwargs):
		try:
			callableObj(*args, **kwargs)
			self.fail("no error was raised")
		except excClass as e:
			if e.code != errorCode:
				self.fail("wrong error code")


	def create_site_if_missing(self):
		try:
			self.proxy_holder.backend_core.site_info(self.host_site_name)
		except UserError as e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise
			self.proxy_holder.backend_core.site_create(self.host_site_name,
			                                          self.default_organization_name,
			                                          self.host_site_name)

	def delete_site_if_exists(self):
		try:
			self.proxy_holder.backend_api.site_remove(self.host_site_name)
		except UserError, e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise

	def get_host_name(self, address):
		"""
		resolve a host address to a name (to be used as identifier in tomato)
		:param str address: host address
		:return: host name
		:rtype: str
		"""
		return address.replace(".", "_")

	def add_host_if_missing(self, address):
		self.create_site_if_missing()
		try:
			self.proxy_holder.backend_core.host_info(self.get_host_name(address))
		except UserError, e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise
			self.proxy_holder.backend_core.host_create(self.get_host_name(address), self.host_site_name,
		                                          {
			                                          'rpcurl': "ssl+jsonrpc://%s:8003"%address,
		                                            'address': address
		                                          })

	def remove_host_if_available(self, address):
		try:
			self.proxy_holder.backend_api.host_remove(self.get_host_name(address))
		except UserError, e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise

	def remove_all_other_accounts(self):
		for user in self.proxy_holder.backend_users.user_list():
			if user["name"] != self.proxy_holder.username:
				self.proxy_holder.backend_users.user_remove(user["name"])

	def remove_all_other_organizations(self):
		for orga in self.proxy_holder.backend_users.organization_list():
			if orga["name"] != self.default_organization_name:
				self.proxy_holder.backend_users.organization_remove(orga["name"])

	def set_user(self, username, organization, email, password, realname, flags):
		"""
		create user if missing.
		set params if existing.
		:param str username:
		:param str organization:
		:param str email:
		:param str password:
		:param str realname:
		:param list(str) flags: all flags that the user shall have
		:return:
		"""
		try:
			self.proxy_holder.backend_users.user_create(username, organization, email, password, {
				"realname": realname,
				"flags": {f: f in flags for f in userflags.iterkeys()}
			})
		except UserError, e:
			if e.code != UserError.ALREADY_EXISTS:
				raise
			self.proxy_holder.backend_users.user_modify({
				"organization": organization,
				"email": email,
				"password": password,
				"realname": realname,
				"flags": {f: f in flags for f in userflags.iterkeys()}
			})
