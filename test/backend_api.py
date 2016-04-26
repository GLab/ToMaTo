from proxies import ProxyHoldingTestCase
import unittest

class GeneralTestCase(ProxyHoldingTestCase):
	def test_ping(self):
		self.assertTrue(self.proxy_holder.backend_api.debug_services_reachable()["backend_api"])




def suite():
	general = unittest.TestLoader().loadTestsFromTestCase(GeneralTestCase)
	return unittest.TestSuite([general])
