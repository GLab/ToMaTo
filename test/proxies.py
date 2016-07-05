#!/usr/bin/python

# this script can execute tests.
# assumption: the API can be reached at localhost:8000 with user admin:changeme

import sys
import unittest
import json
import subprocess
import time

TOMATO_BACKEND_API_MODULE = "backend_api"
TOMATO_MODULES = ("backend_api", "backend_accounting", "backend_core", "backend_debug", "backend_users")

sys.path.insert(1, "../cli/")
import lib as tomato
from lib.error import UserError
from lib.userflags import flags as userflags
import json
import os, base64, hashlib, copy


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

	def get_proxy(self, tomato_module):
		return getattr(self, tomato_module)


proxy_holder = ProxyHolder("admin", "changeme")
with open("testhosts.json") as f:
	test_hosts = json.load(f)
with open("testtemplates.json") as f:
	test_templates = json.load(f)

class ProxyHoldingTestCase(unittest.TestCase):
	"""
	:type proxy_holder: ProxyHolder
	:type test_host_addresses: list(str)
	"""


	"""
	Proxyholder for admin user
	"""
	proxy_holder = proxy_holder
	"""
	ProxyHolder for unqualified user (used in most TestCases for unauthorized access)
	"""
	proxy_holder_tester = None


	host_site_name = "testhosts"
	default_organization_name = "others"
	default_user_name = "admin"
	default_profile_name = "normal"
	test_host_addresses = test_hosts
	test_temps = copy.deepcopy(test_templates)


	def __init__(self, methodName='runTest'):
		super(ProxyHoldingTestCase, self).__init__(methodName)

	@classmethod
	def assertRaisesError(cls,excClass, errorCode, callableObj=None, *args, **kwargs):
		try:
			callableObj(*args, **kwargs)
			cls.fail("no error was raised")
		except excClass as e:
			if e.code != errorCode:
				cls.fail("wrong error code")

	@classmethod
	def create_site_if_missing(cls):
		try:
			proxy_holder.backend_core.site_info(cls.host_site_name)
		except UserError as e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise
			proxy_holder.backend_core.site_create(cls.host_site_name,
												  	cls.default_organization_name,
												  	cls.host_site_name)

	@classmethod
	def delete_site_if_exists(cls):
		try:
			proxy_holder.backend_core.site_remove(cls.host_site_name)
		except UserError, e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise

	@classmethod
	def get_host_name(cls, address):
		"""
		resolve a host address to a name (to be used as identifier in tomato)
		:param str address: host address
		:return: host name
		:rtype: str
		"""
		return address.replace(".", "_")

	@classmethod
	def add_host_if_missing(cls, address):
		"""
		Check if host is already added, otherwise add him
		:param str address: host address
		"""
		cls.create_site_if_missing()
		try:
			proxy_holder.backend_core.host_info(cls.get_host_name(address))
		except UserError, e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise
			proxy_holder.backend_core.host_create(cls.get_host_name(address), cls.host_site_name,
		                                          {
			                                          'rpcurl': "ssl+jsonrpc://%s:8003"%address,
		                                            'address': address
		                                          })

	@classmethod
	def remove_host_if_available(cls, address):
		try:
			proxy_holder.backend_core.host_remove(cls.get_host_name(address))
		except UserError, e:
			if e.code != UserError.ENTITY_DOES_NOT_EXIST:
				raise

	#Requires available test hosts
	@classmethod
	def add_templates_if_missing(cls):
		template_list = proxy_holder.backend_core.template_list()
		#if the template list is empty, use the api to add all test templates
		if(template_list == []):
			templates = copy.deepcopy(cls.test_temps)
			for template in templates:
				tech = template['tech']
				name = template['name']
				del template['tech']
				del template['name']
				attrs = template
				proxy_holder.backend_core.template_create(tech, name, attrs)

		template_ready_on_backend = 0
		template_list = proxy_holder.backend_core.template_list()

		print "\nWaiting for backend to load all templates..."
		while template_ready_on_backend < len(template_list):
			template_list = proxy_holder.backend_core.template_list()
			template_ready_on_backend = 0
			for template in template_list:
				if template['ready']['backend']:
					template_ready_on_backend += 1
			time.sleep(1)

		for host in proxy_holder.backend_core.host_list():
			proxy_holder.backend_core.host_action(host['name'], "forced_update")
			proxy_holder.backend_core.host_action(host['name'], "forced_update")

	@classmethod
	def add_profiles(cls):
		for temp in cls.test_temps:
			# Create test profile for openvz
			testprofile_tech = temp['tech']
			testprofile_name = cls.default_profile_name
			testprofile_args = {'diskspace': 10240, 'restricted': False, 'ram': 512, 'cpus': 1.0, 'label': 'Normal',
									'preference': 10, 'description': 'Test profile'}

			cls.proxy_holder.backend_core.profile_create(testprofile_tech, testprofile_name,
														 testprofile_args)



	@classmethod
	def remove_all_other_accounts(cls):
		for user in proxy_holder.backend_users.user_list():
			if user["name"] != proxy_holder.username:
				proxy_holder.backend_users.user_remove(user["name"])

	@classmethod
	def remove_all_profiles(cls):
		for profile in proxy_holder.backend_core.profile_list():
			proxy_holder.backend_core.profile_remove(profile["id"])

	@classmethod
	def remove_all_templates(cls):
		for template in proxy_holder.backend_core.template_list():
			proxy_holder.backend_core.template_remove(template["id"])

	@classmethod
	def remove_all_networks(cls):
		for network in proxy_holder.backend_core.network_list():
			proxy_holder.backend_core.network_remove(network["id"])

	@classmethod
	def remove_all_network_instances(cls):
		for network_instance in proxy_holder.backend_core.network_instance_list():
			proxy_holder.backend_core.network_instance_remove(network_instance['id'])

	@classmethod
	def remove_all_other_sites(cls):
		for site in proxy_holder.backend_core.site_list():
			proxy_holder.backend_core.site_remove(site["name"])

	@classmethod
	def remove_all_other_organizations(cls):
		for orga in proxy_holder.backend_api.organization_list():
			if orga["name"] != cls.default_organization_name:
				proxy_holder.backend_api.organization_remove(orga["name"])

	@classmethod
	def remove_all_hosts(cls):
		for host in proxy_holder.backend_core.host_list():
			proxy_holder.backend_core.host_remove(host["name"])

	@classmethod
	def remove_all_topologies(cls):
		for topology in proxy_holder.backend_core.topology_list():
			proxy_holder.backend_core.topology_remove(topology["id"])

	@classmethod
	def remove_all_elements(cls):
		topologies = proxy_holder.backend_core.topology_list()
		for topology in topologies:
			proxy_holder.backend_core.topology_action(topology['id'], "destroy")
			while not topology['elements'] == []:
				for element in topology['elements']:
					element_info = proxy_holder.backend_core.element_info(element)
					if element_info['children'] == []:
						proxy_holder.backend_core.element_remove(element)
				topology = proxy_holder.backend_core.topology_info(topology['id'])

	@classmethod
	def remove_all_connections(cls):
		for topology in proxy_holder.backend_core.topology_list():
			for connection in topology['connections']:
				proxy_holder.backend_core.connection_remove(connection)

	@classmethod
	def set_user(cls, username, organization, email, password, realname, flags):
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
			proxy_holder.backend_users.user_create(username, organization, email, password, {
				"realname": realname,
				"flags": {f: f in flags for f in userflags.iterkeys()}
			})
		except UserError, e:
			if e.code != UserError.ALREADY_EXISTS:
				raise
			proxy_holder.backend_users.user_modify({
				"organization": organization,
				"email": email,
				"password": password,
				"realname": realname,
				"flags": {f: f in flags for f in userflags.iterkeys()}
			})
