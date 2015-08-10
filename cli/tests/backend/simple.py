from lib.tests import testCase, testSuite

from topology import setUp, tearDown

@testCase("Dummy Test")
def testDummy(_):
	pass

@testCase("Simple Topology Lifecycle", setUp=setUp, tearDown=tearDown)
def testSimpleTopologyLifecycle(topId):
	print "Creating simple topology..."
	kvm = element_create(topId, "kvmqm")
	kvm_eth0 = element_create(topId, "kvmqm_interface", kvm["id"]) 
	openvz = element_create(topId, "openvz")
	openvz_eth0 = element_create(topId, "openvz_interface", openvz["id"]) 
	switch = element_create(topId, "tinc_vpn") 
	switch_port0 = element_create(topId, "tinc_endpoint", switch["id"])
	switch_port1 = element_create(topId, "tinc_endpoint", switch["id"])
	con0 = connection_create(kvm_eth0["id"], switch_port0["id"])
	con1 = connection_create(openvz_eth0["id"], switch_port1["id"])
	print "Preparing topology..."
	topology_action(topId, "prepare")
	print "Starting topology..."
	topology_action(topId, "start")
	print "Stopping topology..."
	topology_action(topId, "stop")
	print "Destroying topology..."
	topology_action(topId, "destroy")
	
@testCase("Account Flags consistent")
def checkFlagCategoryIntegrity():
	config = account_flag_configuration()
	
	cats = []
	flags_from_cats = []
	for cat in config['categories']:
		assert 'title' in cat and 'onscreentitle' in cat and 'flags' in cat
		assert cat['title'] not in cats #check whether each category occurs only once
		cats.append(cat['title'])
		for flag in cat['flags']:
			assert flag not in flags_from_cats #check whether each flag occurs only once
			flags_from_cats.append(flag)
			
	for f in config['flags']:
		assert f in flags_from_cats #check whether each flag has a category
		
	for f in flags_from_cats:
		assert f in config['flags'] #check whether each category only contains valid flags
	
	
tests = [
	testDummy,
	testSimpleTopologyLifecycle,
	checkFlagCategoryIntegrity
]
	
if __name__ == "__main__":
	testSuite(tests)