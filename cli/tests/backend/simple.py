from lib import testCase

@testCase("Dummy Test")
def testDummy(topId):
	pass

@testCase("Simple Topology Lifecycle")
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
	
if __name__ == "__main__":
	testDummy()
	testSimpleTopologyLifecycle()