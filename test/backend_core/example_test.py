from proxies import ProxyHoldingTestCase
import unittest

class GeneralTestCase(ProxyHoldingTestCase):
	def test_ping(self):
		self.assertTrue(self.proxy_holder.backend_core.ping())




def suite():
	general = unittest.TestLoader().loadTestsFromTestCase(GeneralTestCase)
	return unittest.TestSuite([general])
