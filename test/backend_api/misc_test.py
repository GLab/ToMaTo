#!/usr/bin/python

from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.settings import Config
import unittest

# the API tests assume that all other backend services work properly.

"""
### server_info
- Scenario 1: Execute

### statistics
- Scenario 1: Execute
"""


def dict_in_dict(dictA, dictB):
	"""
	check whether dictA is completely in dictB
	:param dict dictA:
	:param dict dictB:
	:return: whether dictA is in dictB
	"""
	for k, v in dictA.iteritems():
		if k not in dictB:
			return False
		if isinstance(v, dict):
			if not isinstance(dictB[k], dict):
				return False
			if not dict_in_dict(v, dictB[k]):
				return False
		else:
			if v != dictB[k]:
				return False
	return True


class MiscTestCase(ProxyHoldingTestCase):
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_server_info(self):
		res = self.proxy_holder.backend_api.server_info()
		self.assertTrue("public_key" in res)
		self.assertTrue("version" in res)
		self.assertTrue("api_version" in res)
		self.assertTrue("topology_timeout" in res)
		self.assertTrue("TEMPLATE_TRACKER_URL" in res)

	def test_statistics(self):
		res = self.proxy_holder.backend_api.statistics()
		self.assertTrue("usage" in res)
		self.assertTrue("resources" in res)
		for module in Config.TOMATO_BACKEND_INTERNAL_REACHABLE_MODULES:
			res_intern = self.proxy_holder.get_proxy(module).statistics()
			self.assertTrue(dict_in_dict(res_intern, res))


def suite():
	return unittest.TestSuite([
		unittest.TestLoader().loadTestsFromTestCase(MiscTestCase)
	])
