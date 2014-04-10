from lib import testCase, testSuite, unicodeTestString, createStarTopology

def setUp(name):
	print "Creating topology..."
	topInfo = topology_create()
	topId = topInfo["id"]
	print "Topology ID: %d" % topId
	topology_modify(topId, {"name": "Test: %s" % name})
	return topId

def tearDown(topId):
	if not topId:
		return
	print "Destroying topology..."
	topology_action(topId, "destroy")
	print "Removing topology..."
	topology_remove(topId)
	print "Done"

@testCase("api.topology_permissions")
def testTopologyPermissions(_):
	print "Calling topology_permissions..."
	res = topology_permissions()
	assert "owner" in res, "Permissions did not contain owner"

@testCase("api.topology_modify", setUp=setUp, tearDown=tearDown)
def testTopologyModify(topId):
	print "Changing name of topology..."
	top = topology_info(topId)
	assert top["attrs"]["name"] != "test", "Topology already named test"
	top = topology_modify(topId, {"name": "test"})
	assert top["attrs"]["name"] == "test", "Attribute did not change"
	assert top == topology_info(topId), "Return value of modify was different from topology_info"
	print "Trying to set an unspecified attribute..."
	try:
		topology_modify(topId, {"xname": "test"})
		assert False, "Setting undefined attribute succeeded"
	except:
		pass
	print "Setting a user-defined attribute..."
	top = topology_modify(topId, {"_test": "test"})
	assert "_test" in top["attrs"] and top["attrs"]["_test"] == "test", "Unable to set user-defined attribute"
	print "Testing unicode..."
	top = topology_modify(topId, {"_unicode": unicodeTestString})
	assert top["attrs"]["_unicode"] == unicodeTestString, "Unicode string has been altered"

@testCase("api.topology_info", setUp=setUp, tearDown=tearDown)
def testTopologyInfo(topId):
	createStarTopology(topId)
	print "Calling topology_info..."
	top = topology_info(topId)
	
@testCase("api.topology_action", setUp=setUp, tearDown=tearDown)
def testTopologyAction(topId):
	createStarTopology(topId)
	print "Calling action prepare..."
	topology_action(topId, "prepare")
	print "Calling action start..."
	topology_action(topId, "start")
	print "Calling action stop..."
	topology_action(topId, "stop")
	print "Calling action destroy..."
	topology_action(topId, "destroy")

@testCase("api.topology_list")
def testTopologyList(_):
	res = topology_list()
	assert isinstance(res, list), "List was no list"
	assert len(res) >= 1, "List was empty" 

@testCase("api.topology_export", setUp=setUp, tearDown=tearDown)
def testTopologyExport(topId):
	createStarTopology(topId)
	print "Exporting topology..."
	res = topology_export(topId)
	assert res, "Exporting topology did not return anything"

@testCase("api.topology_import", setUp=setUp, tearDown=tearDown)
def testTopologyImport(topId):
	createStarTopology(topId, 3)
	print "Exporting topology..."
	data = topology_export(topId)
	print "Importing topology..."
	(top_id, elements, connections, errors) = topology_import(data)
	topology_remove(top_id)
	assert not errors, "Import resulted in errors: %s" % errors
	assert len(elements) == 10, "Imported topology was malformed"
	assert len(connections) == 3, "Imported topology was malformed"
	
tests = [
	testTopologyPermissions,
	testTopologyModify,
	testTopologyInfo,
	testTopologyAction,
	testTopologyList,
	testTopologyExport,
	testTopologyImport
]

if __name__ == "__main__":
	testSuite(tests)