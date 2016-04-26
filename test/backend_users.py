from proxies import ProxyHoldingTestCase, UserError
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

	def test_host_example(self):
		self.create_site_if_missing()
		self.assertEqual(self.host_site_name, self.proxy_holder.backend_api.site_info(self.host_site_name)["name"])
		for address in self.test_host_addresses:
			self.add_host_if_missing(address)
			self.assertEqual(self.proxy_holder.backend_api.host_info(self.get_host_name(address))["address"], address)
			self.add_host_if_missing(address)
			self.remove_host_if_available(address)
			self.assertRaises(UserError, self.proxy_holder.backend_api.host_info(self.get_host_name(address)))
		self.delete_site_if_exists()




def suite():
	general = unittest.TestLoader().loadTestsFromTestCase(GeneralTestCase)
	example = unittest.TestLoader().loadTestsFromTestCase(ExampleUserTestCase)
	return unittest.TestSuite([general, example])
