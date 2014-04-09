from lib import testCase, testSuite, unicodeTestString

def randomName():
	import uuid
	return str(uuid.uuid4())

@testCase("api.organization_list()", withoutTopology=True)
def testOrganizationList():
	print "Retrieving organization list..."
	res = organization_list()
	assert res, "No organizations returned"
	
@testCase("api.organization_info()", withoutTopology=True)
def testOrganizationInfo():
	print "Retrieving organization list..."
	res = organization_list()
	print "Retrieving information on one organization..."
	info = organization_info(res[0]["name"])
	assert info, "No information returned"
	assert info == res[0], "Info was different from the list entry"

@testCase("api.organization_create()", withoutTopology=True, requiredFlags=["global_admin"])
def testOrganizationCreate():
	name = randomName()
	print "Random organization name: %s" % name
	try:
		print "Creating organization..."
		organization_create(name, "Just a test")
		info = organization_info(name)
		assert info, "Organization has not been created"
	finally:
		try:
			print "Removing organization..."
			organization_remove(name)
		except:
			pass

@testCase("api.organization_modify()", withoutTopology=True, requiredFlags=["global_admin"])
def testOrganizationModify():
	name = randomName()
	print "Random organization name: %s" % name
	try:
		print "Creating organization..."
		organization_create(name, "Just a test")
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
	finally:
		try:
			print "Removing organization..."
			organization_remove(name)
		except:
			pass

@testCase("api.organization_remove()", withoutTopology=True, requiredFlags=["global_admin"])
def testOrganizationRemove():
	name = randomName()
	print "Random organization name: %s" % name
	try:
		print "Creating organization..."
		organization_create(name, "Just a test")
	finally:
		try:
			print "Removing organization..."
			organization_remove(name)
		except:
			pass

@testCase("api.organization_usage()", withoutTopology=True, requiredFlags=["global_admin"])
def testOrganizationUsage():
	name = randomName()
	print "Random organization name: %s" % name
	try:
		print "Creating organization..."
		organization_create(name, "Just a test")
		print "Requesting resource statistics..."
		usage = organization_usage(name)
		assert usage, "No usage information"
	finally:
		try:
			print "Removing organization..."
			organization_remove(name)
		except:
			pass

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