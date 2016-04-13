from .. import scheduler
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

def debug(method, args=None, kwargs=None, profile=None):
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()
