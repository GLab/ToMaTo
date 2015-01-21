from lib.tests import testCase, testSuite, unicodeTestString

from organization import setUp as setUpOrga, tearDown as tearDownOrga, randomName

def setUp(name):
	orga = setUpOrga(name)
	print "Creating site..."
	site = randomName()
	site_create(site, orga, "Just a test")
	return site

def tearDown(site):
	print "Removing site..."
	info = site_info(site)
	site_remove(site)
	tearDownOrga(info["organization"])

@testCase("api.site_list")
def testSiteList(_):
	print "Retrieving site list..."
	res = site_list()
	assert res, "No sites returned"
	
@testCase("api.site_info")
def testSiteInfo(_):
	print "Retrieving site list..."
	res = site_list()
	print "Retrieving information on one site..."
	info = site_info(res[0]["name"])
	assert info, "No information returned"
	assert info == res[0], "Info was different from the list entry"

@testCase("api.site_create", setUp=setUp, tearDown=tearDown, requiredFlags=["global_admin"])
def testSiteCreate(name):
	info = site_info(name)
	assert info, "Site has not been created"

@testCase("api.site_modify", setUp=setUp, tearDown=tearDown, requiredFlags=["global_admin"])
def testSiteModify(name):
	print "Modifying site..."
	info = site_modify(name, {
		"description": "Just a test",
		"location": "Neverland",
		"geolocation": {"latitude": 80, "longitude": -20.3},
		"description_text": "Please ignore"
	})
	assert info["description_text"] == "Please ignore", "Modify did not work"
	print "Testing unicode..."
	info = site_modify(name, {"description": unicodeTestString})
	assert info["description"] == unicodeTestString, "Unicode string has been altered"		

@testCase("api.site_remove", setUp=setUpOrga, tearDown=tearDownOrga, requiredFlags=["global_admin"])
def testSiteRemove(orga):
	print "Creating site..."
	site = randomName()
	site_create(site, orga, "Just a test")
	print "Removing site..."
	site_remove(site)

tests = [
	testSiteList,
	testSiteInfo,
	testSiteCreate,
	testSiteModify,
	testSiteRemove,
]

if __name__ == "__main__":
	testSuite(tests)