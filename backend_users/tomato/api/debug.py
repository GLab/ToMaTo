from .. import scheduler
import traceback, sys

def ping():
	return True

def debug_stats():
	from .. import database_obj
	stats = {}
	stats["db"] = database_obj.command("dbstats")
	stats["db"]["collections"] = {name: database_obj.command("collstats", name) for name in database_obj.collection_names()}
	stats["scheduler"] = scheduler.info()
	stats["threads"] = map(traceback.extract_stack, sys._current_frames().values())
	return stats

def debug(method, args=None, kwargs=None, profile=None):
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()