from lib import testCase, testSuite, unicodeTestString

def findTask(method):
	for t in task_list():
		if t["method"] == method:
			return t

def waitForTask(method):
	import time
	while True:
		task = findTask(method)
		assert task, "Task not found"
		if not task["busy"]:
			return
		time.sleep(1.0)

def runTask(method):
	task = findTask(method)
	assert task, "Task not found"
	if task["busy"]:
		print "Waiting for task to finish..."
		waitForTask(method)
	print "Running task..."
	ret = task_execute(task["id"])
	assert ret, "Task did not execute successfully"
	

@testCase("tomato.accounting.aggregate()", requiredFlags=["global_admin"])
def testAccountingTask():
	runTask("tomato.accounting.aggregate")
	 
@testCase("tomato.host.synchronize()", requiredFlags=["global_admin"])
def testHostSyncTask():
	runTask("tomato.host.synchronize")

@testCase("tomato.host.synchronizeComponents()", requiredFlags=["global_admin"])
def testHostComponentSyncTask():
	runTask("tomato.host.synchronizeComponents")

@testCase("tomato.auth.cleanup()", requiredFlags=["global_admin"])
def testAuthCleanupTask():
	runTask("tomato.auth.cleanup")

@testCase("tomato.topology.timeout_task()", requiredFlags=["global_admin"])
def testTopologyTimeoutTask():
	runTask("tomato.topology.timeout_task")

@testCase("tomato.link.taskRun()", requiredFlags=["global_admin"])
def testLinkStatisticsTask():
	runTask("tomato.link.taskRun")

@testCase("tomato.elements.*.syncRexTFV()", requiredFlags=["global_admin"])
def testRexTFVTask():
	runTask("tomato.elements.openvz.syncRexTFV")
	runTask("tomato.elements.kvmqm.syncRexTFV")

	 
tests = [
	testAccountingTask,
	testHostSyncTask,
	testHostComponentSyncTask,
	testAuthCleanupTask,
	testTopologyTimeoutTask,
	testLinkStatisticsTask,
	testRexTFVTask
]

if __name__ == "__main__":
	testSuite(tests)