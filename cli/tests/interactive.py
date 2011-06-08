from lib.misc import *

from tests.top.simple import top

from datetime import datetime

errors_remove()
topId = top_create()
try:
	top_modify(topId, jsonToMods(top), True)
	print "Topology %d is created" % topId
	shell()
	task = top_action(topId, "prepare")
	waitForTask(task, assertSuccess=True)
	print "Topology %d is prepared" % topId
	shell()
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	print "Topology %d is started" % topId
	shell()
	task = top_action(topId, "destroy")
	waitForTask(task, assertSuccess=True)
	print "Topology %d is destroyed" % topId
except:
	errors_print()
	shell()
finally:
	top_action(topId, "remove", direct=True)
	