from lib import testCase, testSuite, unicodeTestString

def randomName():
	import uuid
	return str(uuid.uuid4())

def setUp(name):
	name = randomName()
	print "Random organization name: %s" % name
	print "Creating organization..."
	organization_create(name, "Just a test")
	return name

def tearDown(name):
	print "Removing organization..."
	organization_remove(name)

@testCase("api.organization_list")
def testOrganizationList(_):
	print "Retrieving organization list..."
	res = organization_list()
	assert res, "No organizations returned"
	
@testCase("api.organization_info")
def testOrganizationInfo(_):
	print "Retrieving organization list..."
	res = organization_list()
	print "Retrieving information on one organization..."
	info = organization_info(res[0]["name"])
	assert info, "No information returned"
	assert info == res[0], "Info was different from the list entry"

@testCase("api.organization_create", setUp=setUp, tearDown=tearDown, requiredFlags=["global_admin"])
def testOrganizationCreate(name):
	info = organization_info(name)
	assert info, "Organization has not been created"

@testCase("api.organization_modify", setUp=setUp, tearDown=tearDown, requiredFlags=["global_admin"])
def testOrganizationModify(name):
	print "Modifying organization..."
	info = organization_modify(name, {
		"description": "Just a test",
		"homepage_url": "www.example.com",
		"image_url": None,
		"description_text": "Please ignore"
	})
	assert info["description_text"] == "Please ignore", "Modify did not work"
	print "Testing unicode..."
	info = organization_modify(name, {"description": unicodeTestString})
	assert info["description"] == unicodeTestString, "Unicode string has been altered"		

@testCase("api.organization_remove", setUp=setUp, requiredFlags=["global_admin"])
def testOrganizationRemove(name):
	print "Removing organization..."
	organization_remove(name)

@testCase("api.organization_usage", setUp=setUp, tearDown=tearDown, requiredFlags=["global_admin"])
def testOrganizationUsage(name):
	print "Requesting resource statistics..."
	usage = organization_usage(name)
	assert usage, "No usage information"

tests = [
	testOrganizationList,
	testOrganizationInfo,
	testOrganizationCreate,
	testOrganizationModify,
	testOrganizationRemove,
	testOrganizationUsage,
]

if __name__ == "__main__":
	testSuite(tests)