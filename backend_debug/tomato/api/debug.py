from .. import scheduler
from ..lib.debug import run
import traceback, sys

def ping():
	return True

def debug_stats():
	from .. import database_obj
	stats = {
		"db": database_obj.command("dbstats"),
		"scheduler": scheduler.info(),
		"threads": map(traceback.extract_stack, sys._current_frames().values())
	}
	stats["db"]["collections"] = {name: database_obj.command("collstats", name) for name in
	                              database_obj.collection_names()}
	return stats

def debug_debug_internal_api_call(_command, args=None, kwargs=None, profile=True):
	from .. import api
	func = getattr(api, _command)
	result = run(func, args, kwargs, profile)
	return result.marshal()


def debug_execute_task(task_id):
	return scheduler.executeTask(task_id, force=True)
