from lib import testSuite

import element, connection, topology, tasks, organization, sites

tests = element.tests + connection.tests + topology.tests + tasks.tests + organization.tests + sites.tests

if __name__ == "__main__":
	testSuite(tests)
