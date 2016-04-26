from proxies import ProxyHoldingTestCase
import unittest

class GeneralTestCase(ProxyHoldingTestCase):
	def test_ping(self):
		self.assertTrue(self.proxy_holder.backend_users.ping())


class ExampleUserTestCase(ProxyHoldingTestCase):
	# todo: remove this example.

	def test_exists(self):
		self.assertTrue(self.proxy_holder.backend_users.user_exists("admin"))

	def test_notexists(self):
		self.assertRaises(Exception, self.proxy_holder.backend_users.user_exists, "adminfjdkahfdlkshfsklfhjkdsl")





def suite():
	general = unittest.TestLoader().loadTestsFromTestCase(GeneralTestCase)
	example = unittest.TestLoader().loadTestsFromTestCase(ExampleUserTestCase)
	return unittest.TestSuite([general, example])
