from lib import testCase, testSuite

@testCase("dummy")
def testDummy(topId):
	print "Doing something important"
	assert False, "Do not use this dummy test"
	
tests = [
	testDummy
]

if __name__ == "__main__":
	testSuite(tests)