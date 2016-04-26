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
	__slots__ = TOMATO_MODULES

	def __init__(self):
		self.backend_api = tomato.getConnection(tomato.createUrl("http+xmlrpc", "localhost", 8000, "admin", "changeme"))
		for module in TOMATO_MODULES:
			if module != TOMATO_BACKEND_API_MODULE:
				setattr(self, module, InternalAPIProxy(self.backend_api, module))


proxy_holder = ProxyHolder()
with open("testhosts.json") as f:
	test_hosts = json.load(f)
class ProxyHoldingTestCase(unittest.TestCase):
	"""
	:type proxy_holder: ProxyHolder
	:type test_host_addresses: list(str)
	"""
	def setUp(self):
		self.proxy_holder = proxy_holder
		self.test_host_addresses = test_hosts
		self.host_site_name = "testhosts"

	def create_site_if_missing(self):
		try:
			self.proxy_holder.backend_api.site_info(self.host_site_name)
		except UserError as e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise
			self.proxy_holder.backend_api.site_create(self.host_site_name,
			                                          self.proxy_holder.backend_api.organization_list()[0]['name'],
			                                          self.host_site_name)

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
		self.proxy_holder.backend_api.host_create(self.get_host_name(address), self.host_site_name,
		                                          {
			                                          'rpcurl': "ssl+jsonrpc://%s:8003"%address,
		                                            'address': address
		                                          })
