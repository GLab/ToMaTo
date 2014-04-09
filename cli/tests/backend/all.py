from lib import testSuite

import element, connection, topology, tasks

tests = element.tests + connection.tests + topology.tests + tasks.tests

if __name__ == "__main__":
	testSuite(tests)