from lib.misc import *
import time

def simpleTop_checkLinkEmulation(topId):
	#make sure topology is started
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	# throw away the first few samples
	i = 0
	while i < 10 and not link_info(topId, "openvz1", "10.0.0.2", samples=10):
		i += 1
		time.sleep(0.1)
	i = 0
	while i < 10 and not link_info(topId, "openvz2", "10.0.0.1", samples=10):
		i += 1
		time.sleep(0.1)
	# set link config to 0
	link_config(topId, "switch1", "openvz1.eth0", {"delay_to": 0, "delay_from":0, "lossratio_to": 0, "lossratio_from": 0}) 
	link_config(topId, "switch1", "openvz2.eth0", {"delay_to": 0, "delay_from":0, "lossratio_to": 0, "lossratio_from": 0})
	# first test with loss=0 and delay=0
	li = link_info(topId, "openvz1", "10.0.0.2", samples=100)
	assert li
	assert li["lossratio"] == 0.0, "Lossratio should be %s but was %s" %(0.0, li["lossratio"])
	assert li["delay"] <= 1.0, "Delay should be %s but was %s" %(0.0, li["delay"])
	# delay=10ms
	link_config(topId, "switch1", "openvz2.eth0", {"delay_to": 10})
	li = link_info(topId, "openvz2", "10.0.0.1", samples=100)
	assert li
	assert li["lossratio"] == 0.0, "Lossratio should be %s but was %s" %(0.0, li["lossratio"])
	assert abs(li["delay"] - 10) < 1.0, "Delay should be %s but was %s" %(10.0, li["delay"])
	# delay+=15ms
	link_config(topId, "switch1", "openvz1.eth0", {"delay_to": 15})
	li = link_info(topId, "openvz1", "10.0.0.2", samples=100)
	assert li
	assert li["lossratio"] == 0.0, "Lossratio should be %s but was %s" %(0.0, li["lossratio"])
	assert abs(li["delay"] - 25) < 1.0, "Delay should be %s but was %s" %(25.0, li["delay"])
	# loss=30%
	link_config(topId, "switch1", "openvz1.eth0", {"lossratio_from": 30.0})
	li = link_info(topId, "openvz1", "10.0.0.2", samples=250)
	assert li
	assert abs(li["lossratio"] - 0.3) < 0.1, "Lossratio should be %s but was %s" %(0.3, li["lossratio"])
	# loss=10%
	link_config(topId, "switch1", "openvz1.eth0", {"lossratio_from": 10.0})
	li = link_info(topId, "openvz2", "10.0.0.1", samples=250)
	assert li
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
	