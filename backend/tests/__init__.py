import os
os.environ['GLABNETMAN_TESTING']="true"

import hosts, templates, kvm, openvz, tinc, topology

def wait_for_tasks(api, user):
	import time
	while tasks_running(api, user):
		time.sleep(0.1)
	
def tasks_running(api, user):
	count=0
	for t in api.task_list(user=user):
		if t["active"]:
			count+=1
	return count