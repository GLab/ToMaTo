from lib.misc import *
import time, os, socket

def checkPeriodicTasks():
	periodic_tasks = []
	for t in task_list():
		if t.get("periodic", False):
			periodic_tasks.append(t["name"])
		assert t["status"] in ["waiting", "succeeded", "aborted", "failed"], "Tasks running: %s" % t["name"]
	for t in periodic_tasks:
		print "\t" + t
		id = task_run(t)
		waitForTask(id, assertSuccess=True)
		
			

if __name__ == "__main__":
	errors_remove()
	try:
		print "testing periodic tasks..."
		checkPeriodicTasks()
	except:
		import traceback
		traceback.print_exc()
		print "-" * 50
		errors_print()
		print "-" * 50
		raw_input("Press enter to continue")	