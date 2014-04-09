from lib import testSuite

import element, connection, topology, tasks, organization

tests = element.tests + connection.tests + topology.tests + tasks.tests + organization.tests

if __name__ == "__main__":
	testSuite(tests)
