from lib import testCase, testSuite, unicodeTestString

from topology import setUp, tearDown

def prepare(topId, createConnection=True):
	print "Creating 2 elements..."
	el1 = element_create(topId, "openvz")
	el1_id = el1["id"]
	if1 = element_create(topId, "openvz_interface", el1_id)
	if1_id = if1["id"]
	el2 = element_create(topId, "openvz")
	el2_id = el2["id"]
	if2 = element_create(topId, "openvz_interface", el2_id)
	if2_id = if2["id"]
	if createConnection:
		print "Creating a connection..."
		con = connection_create(if1_id, if2_id)
		con_id = con["id"]
		return el1_id, el2_id, if1_id, if2_id, con_id
	else:
		return el1_id, el2_id, if1_id, if2_id, None

@testCase('api.connection_create()', setUp=setUp, tearDown=tearDown)
def testConnectionCreate(topId):
	el1_id, el2_id, if1_id, if2_id, con_id = prepare(topId, createConnection=False)
	print "Creating a connection..."
	con = connection_create(if1_id, if2_id)
	assert "id" in con, "No id in create_connection return value"
	con_id = con["id"]
	assert con == connection_info(con_id), "Return value of connection_create was different from connection_info"
	
@testCase('api.connection_remove()', setUp=setUp, tearDown=tearDown)
def testConnectionRemove(topId):
	el1_id, el2_id, if1_id, if2_id, con_id = prepare(topId)
	connection_remove(con_id)
	top = topology_info(topId)
	assert not top["connections"], "Connection exists after connection_remove"

@testCase("api.connection_info()", setUp=setUp, tearDown=tearDown)
def testConnectionInfo(topId):
	el1_id, el2_id, if1_id, if2_id, con_id = prepare(topId, createConnection=False)
	print "Creating a connection..."
	con = connection_create(if1_id, if2_id)
	con_id = con["id"]
	print "Checking connection info..."
	con_info = connection_info(con_id)
	assert con_info == con, "Connection info does not contain full information"
	print "Fetching connection info..."
	con_info = connection_info(con_id, fetch=True)

@testCase("api.connection_action()", setUp=setUp, tearDown=tearDown)
def testConnectionAction(topId):
	el1_id, el2_id, if1_id, if2_id, con_id = prepare(topId)
	print "Enabling packet capturing on connection..."
	connection_modify(con_id, {"capturing": True})
	print "Starting topology..."
	topology_action(topId, "start")
	print "Generating some traffic..."
	element_action(el1_id, "execute", {"cmd": "ping 10.0.0.2 -c 1 -w 1; true"})
	print "Executing action download_grant on connection..."
	connection_action(con_id, "download_grant")

@testCase("api.connection_usage()", setUp=setUp, tearDown=tearDown)
def testConnectionUsage(topId):
	el1_id, el2_id, if1_id, if2_id, con_id = prepare(topId)
	print "Fetching resource statistics..."
	usage = connection_usage(con_id)

@testCase("api.connection_modify()", setUp=setUp, tearDown=tearDown)
def testConnectionModify(topId):
	el1_id, el2_id, if1_id, if2_id, con_id = prepare(topId)
	con = connection_info(con_id)
	assert con["attrs"]["emulation"] == True, "Link emulation is disabled"
	print "Modifying connection..."
	connection_modify(con_id, {"emulation": False})
	con = connection_info(con_id)
	assert con["attrs"]["emulation"] == False, "Modify did not set the attribute"
	print "Trying to set an unspecified attribute..."
	try:
		connection_modify(con_id, {"xname": "test"})
		assert False, "Setting undefined attribute succeeded"
	except:
		pass
	print "Setting a user-defined attribute..."
	connection_modify(con_id, {"_test": "test"})
	con = connection_info(con_id)
	assert "_test" in con["attrs"] and con["attrs"]["_test"] == "test", "Unable to set user-defined attribute"
	print "Testing unicode..."
	connection_modify(con_id, {"_unicode": unicodeTestString})
	con = connection_info(con_id)
	assert con["attrs"]["_unicode"] == unicodeTestString, "Unicode string has been altered"

tests = [
	testConnectionCreate,
	testConnectionRemove,
	testConnectionInfo,
	testConnectionModify,
	testConnectionAction,
	testConnectionUsage
]

if __name__ == "__main__":
	testSuite(tests)