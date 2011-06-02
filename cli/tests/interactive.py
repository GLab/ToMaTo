from lib.misc import *

from tests.top.simple import top

from datetime import datetime

errors_remove()
topId = top_create()
try:
	top_modify(topId, jsonToMods(top), True)
	raw_input("Press enter to prepare topology")
	task = top_action(topId, "prepare")
	waitForTask(task, assertSuccess=True)
	raw_input("Press enter to start topology")
	task = top_action(topId, "start")
	waitForTask(task, assertSuccess=True)
	raw_input("Press enter to destroy topology")
	task = top_action(topId, "destroy")
	waitForTask(task, assertSuccess=True)
finally:
	top_action(topId, "remove", direct=True)
	errors_print()