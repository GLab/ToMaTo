from lib import testCase, testSuite, unicodeTestString

from topology import setUp, tearDown

@testCase("api.element_create", setUp=setUp, tearDown=tearDown)
def testElementCreate(topId):
	print "Creating simple element..."
	el1 = element_create(topId, "openvz")
	assert "id" in el1, "No id in return value"
	el1_id = el1["id"]
	assert el1 == element_info(el1_id), "Return value was different from element_info: %s vs. %s" % (el1, element_info(el1_id))
	print "Creating preconfigured element..."
	el2 = element_create(topId, "openvz", attrs={"name": "element2"})
	el2_id = el2["id"]
	assert el2 == element_info(el2_id), "Return value was different from element_info: %s vs. %s" % (el2, element_info(el2_id))
	assert "name" in el2["attrs"], "No name in attrs"
	assert el2["attrs"]["name"] == "element2"
	print "Creating a child element..."
	el3 = element_create(topId, "openvz_interface", el2_id)
	assert el3["parent"] == el2_id
	 
@testCase("api.element_modify", setUp=setUp, tearDown=tearDown)
def testElementModify(topId):
	print "Creating element..."
	el = element_create(topId, "openvz")
	el_id = el["id"]
	assert el["attrs"]["name"] != "test", "Element already has the name test"
	print "Modifying element..."
	element_modify(el_id, {"name": "test"})
	el = element_info(el_id)
	assert "name" in el["attrs"] and el["attrs"]["name"] == "test", "Modify did not set the name"
	print "Trying to set an unspecified attribute..."
	try:
		element_modify(el_id, {"xname": "test"})
		assert False, "Setting undefined attribute succeeded"
	except:
		pass
	print "Setting a user-defined attribute..."
	element_modify(el_id, {"_test": "test"})
	el = element_info(el_id)
	assert "_test" in el["attrs"] and el["attrs"]["_test"] == "test", "Unable to set user-defined attribute"
	print "Testing unicode..."
	element_modify(el_id, {"_unicode": unicodeTestString})
	el = element_info(el_id)
	assert el["attrs"]["_unicode"] == unicodeTestString, "Unicode string has been altered"

@testCase("api.element_action", setUp=setUp, tearDown=tearDown)
def testElementAction(topId):
	print "Creating element..."
	el = element_create(topId, "openvz")
	el_id = el["id"]
	assert el["state"] == "created"
	print "Calling action prepare on element..."
	element_action(el_id, "prepare")
	el = element_info(el_id)
	assert el["state"] == "prepared"
	print "Calling action destroy on element..."
	element_action(el_id, "destroy")
	el = element_info(el_id)
	assert el["state"] == "created"

@testCase("api.element_remove", setUp=setUp, tearDown=tearDown)
def testElementRemove(topId):
	print "Creating element..."
	el = element_create(topId, "openvz")
	el_id = el["id"]
	print "Removing element..."
	element_remove(el_id)
	top = topology_info(topId)
	assert not top["elements"], "Element exists after remove"

@testCase("api.element_info", setUp=setUp, tearDown=tearDown)
def testElementInfo(topId):
	print "Creating element..."
	el = element_create(topId, "openvz")
	el_id = el["id"]
	print "Checking element info..."
	el_info = element_info(el_id)
	assert el_info == el, "Element info does not contain full information"
	print "Fetching element info..."
	el_info = element_info(el_id, fetch=True)
	print "Preparing element..."
	element_action(el_id, "prepare")
	print "Fetching element info..."
	el_info = element_info(el_id, fetch=True)

@testCase("api.element_usage", setUp=setUp, tearDown=tearDown)
def testElementUsage(topId):
	print "Creating element..."
	el = element_create(topId, "openvz")
	el_id = el["id"]
	print "Fetching resource statistics..."
	usage = element_usage(el_id)

tests = [
	testElementCreate,
	testElementRemove,
	testElementInfo,
	testElementModify,
	testElementAction,
	testElementUsage
]

if __name__ == "__main__":
	testSuite(tests)