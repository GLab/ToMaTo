from lib.misc import *

def simpleTop_checkLinkEmulation(topId):
	#make sure topology is started
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	# throw away the first few samples
	link_info(topId, "openvz1", "10.0.0.2", samples=10)
	link_info(topId, "openvz2", "10.0.0.1", samples=10)
	# set link config to 0
	link_config(topId, "switch1", "openvz1.eth0", {"delay": 0, "lossratio": "0"}) 
	link_config(topId, "switch1", "openvz2.eth0", {"delay": 0, "lossratio": "0"})
	# first test with loss=0 and delay=0
	li = link_info(topId, "openvz1", "10.0.0.2", samples=100)
	assert li["lossratio"] == 0.0, "Lossratio should be %s but was %s" %(0.0, li["lossratio"])
	assert li["delay"] <= 1.0, "Delay should be %s but was %s" %(0.0, li["delay"])
	# delay=10ms
	link_config(topId, "switch1", "openvz2.eth0", {"delay": 10})
	li = link_info(topId, "openvz2", "10.0.0.1", samples=100)
	assert li["lossratio"] == 0.0, "Lossratio should be %s but was %s" %(0.0, li["lossratio"])
	assert abs(li["delay"] - 10) < 1.0, "Delay should be %s but was %s" %(10.0, li["delay"])
	# delay+=15ms
	link_config(topId, "switch1", "openvz1.eth0", {"delay": 15})
	li = link_info(topId, "openvz1", "10.0.0.2", samples=100)
	assert li["lossratio"] == 0.0, "Lossratio should be %s but was %s" %(0.0, li["lossratio"])
	assert abs(li["delay"] - 25) < 1.0, "Delay should be %s but was %s" %(25.0, li["delay"])
	# loss=30%
	link_config(topId, "switch1", "openvz1.eth0", {"lossratio": 0.3})
	li = link_info(topId, "openvz1", "10.0.0.2", samples=250)
	assert abs(li["lossratio"] - 0.3) < 0.1, "Lossratio should be %s but was %s" %(0.3, li["lossratio"])
	# loss=10%
	link_config(topId, "switch1", "openvz1.eth0", {"lossratio": 0.1})
	li = link_info(topId, "openvz2", "10.0.0.1", samples=250)
	assert abs(li["lossratio"] - 0.1) < 0.1, "Lossratio should be %s but was %s" %(0.1, li["lossratio"])

if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "starting topology..."
		task = top_action(topId, "start")
		waitForTask(task, assertSuccess=True)

		print "testing link emulation..."
		simpleTop_checkLinkEmulation(topId)

		print "destroying topology..."
		top_action(topId, "destroy", direct=True)
	except:
		import traceback
		traceback.print_exc()
		print "-" * 50
		errors_print()
		print "-" * 50
		print "Topology id is: %d" % topId
		raw_input("Press enter to remove topology")
	finally:
		top_action(topId, "remove", direct=True)
	