from .. import scheduler
import traceback, sys
from api_helpers import getCurrentUserInfo
from ..lib.settings import Config
from ..lib.service import is_reachable

def debug(method, args=None, kwargs=None, profile=None):
	getCurrentUserInfo().check_may_view_debugging_info()
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()

def debug_stats(tomato_module):
	getCurrentUserInfo().check_may_view_debugging_info()
	from .. import database_obj
	stats = {}
	stats["db"] = database_obj.command("dbstats")
	stats["db"]["collections"] = {name: database_obj.command("collstats", name) for name in database_obj.collection_names()}
	stats["scheduler"] = scheduler.info()
	stats["threads"] = map(traceback.extract_stack, sys._current_frames().values())
	return stats

def debug_services_reachable():
	return {module: is_reachable(module) for module in Config.TOMATO_BACKEND_MODULES}
