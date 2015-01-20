from lib.tests import testCase, testSuite

@testCase("dummy")
def testDummy():
	print "Doing something important"
	assert False, "Do not use this dummy test"
	
tests = [
	testDummy
]

if __name__ == "__main__":
	testSuite(tests)