from proxies import ProxyHolder, ProxyHoldingTestCase
from lib.error import UserError
import unittest


class ElementTestCase(ProxyHoldingTestCase):

	@classmethod
	def setUpClass(cls):
		cls.remove_all_other_accounts()
		cls.remove_all_templates()

		for host in cls.test_host_addresses:
			cls.add_host_if_missing(host)

		cls.add_templates_if_missing(True)


	def setUp(self):

	def tearDown(self):
		self.remove_all_hosts()

	@classmethod
	def tearDownClass(cls):
		cls.remove_all_hosts()
		cls.remove_all_other_accounts()

	def test_element_list(self):
		print "hello world"