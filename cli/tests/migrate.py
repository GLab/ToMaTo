from lib.misc import *
import time, os

def simpleTop_checkMigrate(topId):
	print "\tbringing topology to prepared state..."
	task = top_action(topId, "prepare")
	waitForTask(task, assertSuccess=True)
	task = top_action(topId, "stop")
	waitForTask(task, assertSuccess=True)
	print "\toffline migration of openvz1..."
	task = top_action(topId, "migrate", "device", "openvz1")
	waitForTask(task, assertSuccess=True)
	print "\toffline migration of kvm1..."
	task = top_action(topId, "migrate", "device", "kvm1")
	waitForTask(task, assertSuccess=True)
	print "\tstarting topology..."
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	#start task on device
	print "\tonline migration of openvz1..."
	top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "screen -d -m"})
	res = top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "pidof SCREEN >/dev/null; echo $?"})	
	assert res == "0\n", "Result was %s" % res
	task = top_action(topId, "migrate", "device", "openvz1")
	waitForTask(task, assertSuccess=True)
	res = top_action(topId, "execute", "device", "openvz1", attrs={"cmd": "pidof SCREEN >/dev/null; echo $?"})	
	assert res == "0\n", "Result was %s" % res
	print "\tonline migration of kvm1..."
	task = top_action(topId, "migrate", "device", "kvm1")
	waitForTask(task, assertSuccess=True)	
	
if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "testing migration..."
		simpleTop_checkMigrate(topId)

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
	