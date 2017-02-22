from .. import scheduler
from ..service_status import service_status, problems
from ..lib.debug import run
from ..lib.error import InternalError
from ..lib.exceptionhandling import wrap_and_handle_current_exception
import traceback, sys

def ping():
	return True

def debug_stats():
	from .. import database_obj
	stats = {
		"db": database_obj.command("dbstats"),
		"scheduler": scheduler.info(),
		"threads": map(traceback.extract_stack, sys._current_frames().values()),
		"system": service_status(),
		"problems": problems()
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

def debug_throw_error(data=None):
	"""
	throw an error that is then dumped.
	:return:
	"""
	try:
		InternalError.check(False, code=InternalError.UNKNOWN, message="Test Dump", todump=True, data=data)
	except:
		wrap_and_handle_current_exception(re_raise=True)
