from lib.misc import *

import stateTransitions
import linkEmulation
import tincConnectors
import packetCapturing
import images
import topInformation
import migrate
import periodicTasks

if __name__ == "__main__":
	from tests.top.simple import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "testing topology information..."
		topInformation.simpleTop_checkTopInformation(topId)

		print "testing state transitions..."
		stateTransitions.simpleTop_checkStateTransitions(topId)

		print "testing images..."
		images.simpleTop_checkImages(topId)

		print "testing tinc connectors..."
		tincConnectors.simpleTop_checkTincConnectors(topId)

		print "testing link emulation..."
		linkEmulation.simpleTop_checkLinkEmulation(topId)

		print "testing packet capturing..."
		packetCapturing.simpleTop_checkPacketCapturing(topId)

		print "testing periodic tasks..."
		periodicTasks.checkPeriodicTasks()

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
	