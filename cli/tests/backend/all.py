from lib import testSuite

import element, connection, topology

tests = element.tests + connection.tests + topology.tests

if __name__ == "__main__":
	testSuite(tests)