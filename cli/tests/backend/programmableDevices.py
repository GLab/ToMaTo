from lib.misc import *
import time, os, socket

def simpleTop_checkProgrammableDevices(topId):
	#make sure topology is started
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	assert link_check(topId, "openvz2", "10.0.0.3")
	

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

		print "testing programmable devices..."
		simpleTop_checkProgrammableDevices(topId)

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
	