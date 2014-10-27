from lib import testSuite

import element, connection, topology, tasks, organization, sites, misc

tests = element.tests + connection.tests + topology.tests + tasks.tests + organization.tests + sites.tests + misc.tests

if __name__ == "__main__":
	testSuite(tests)
