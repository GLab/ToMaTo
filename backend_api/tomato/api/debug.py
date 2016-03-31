from .. import scheduler
import traceback, sys
from api_helpers import getCurrentUserInfo
from ..lib.settings import Config
from ..lib.service import is_reachable, is_self, get_tomato_inner_proxy

def debug(method, args=None, kwargs=None, profile=None):
	getCurrentUserInfo().check_may_view_debugging_info()
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()

def debug_stats(tomato_module=Config.TOMATO_MODULE_BACKEND_API):
	if is_self(tomato_module):
		getCurrentUserInfo().check_may_view_debugging_info()
		stats = {}
		stats["scheduler"] = scheduler.info()
		stats["threads"] = map(traceback.extract_stack, sys._current_frames().values())
		return stats
	else:
		api = get_tomato_inner_proxy(tomato_module)
		return api.debug_stats()

def debug_services_overview():
	res = {}
	for module in Config.TOMATO_BACKEND_MODULES:
		res[module] = {
			'reachable': is_reachable(module)
		}

def debug_services_reachable():
	res = {module: is_reachable(module) for module in Config.TOMATO_BACKEND_MODULES}
	res[Config.TOMATO_MODULE_BACKEND_API] = True
	return res
