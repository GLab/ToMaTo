from lib.misc import *

def simpleTop_checkStateTransitions(topId):
	print "\tpreparing topology..."
	top_action(topId, "prepare", direct=True)

	print "\tdestroying topology..."
	task = top_action(topId, "destroy")
	waitForTask(task, assertSuccess=True)

	#FIXME: also test device/connector calls

	print "\tstarting topology..."
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)

	print "\tdestroying topology..."
	top_action(topId, "destroy", direct=True)

if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "testing link emulation..."
		simpleTop_checkStateTransitions(topId)

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