# -*- coding: utf-8 -*-

from lib.misc import *
import time, os

def checkUnicodeSupport(topId):
	print "\tstarting topology..."
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	print "\tchecking ping..."
	assert link_check(topId, u"外国語の学習と教授", "10.0.0.2")
	
if __name__ == "__main__":
	from tests.top.unicode import top
	errors_remove()
	topId = top_create()
	try:
		print "creating topology..."
		top_modify(topId, jsonToMods(top), True)

		print "testing unicode support..."
		checkUnicodeSupport(topId)

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
	
