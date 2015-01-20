from lib.tests import testCase, testSuite, unicodeTestString

@testCase("api.statistics")
def testStatistics(_):
	print "Retrieving statistics..."
	res = statistics()
	assert res, "No statistics returned"
	
@testCase("api.server_info")
def testServerInfo(_):
	print "Retrieving server info..."
	res = server_info()
	assert res, "No information returned"

tests = [
	testStatistics,
	testServerInfo,
]

if __name__ == "__main__":
	testSuite(tests)