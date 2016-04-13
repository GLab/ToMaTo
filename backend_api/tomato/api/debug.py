from .. import scheduler
import traceback, sys
from api_helpers import getCurrentUserInfo
from ..lib.settings import Config
from ..lib.service import is_reachable, is_self, get_tomato_inner_proxy, get_backend_core_proxy
from ..lib.remote_info import get_host_info

def debug(method, args=None, kwargs=None, profile=None):
	getCurrentUserInfo().check_may_view_debugging_info()
	func = globals().get(method)
	from ..lib import debug
	result = debug.run(func, args, kwargs, profile)
	return result.marshal()

def debug_stats(tomato_module=Config.TOMATO_MODULE_BACKEND_API):
	getCurrentUserInfo().check_may_view_debugging_info()
	if is_self(tomato_module):
		return {
			"scheduler": scheduler.info(),
			"threads": map(traceback.extract_stack, sys._current_frames().values())
		}
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


def debug_run_internal_api_call(_tomato_module, _command, *args, **kwargs):
	getCurrentUserInfo().check_allow_active_debugging()
	return get_tomato_inner_proxy(_tomato_module)._call(_command, args, kwargs)

def debug_run_host_api_call(host_name, _command, *args, **kwargs):
	getCurrentUserInfo().check_allow_active_debugging()
	getCurrentUserInfo().check_may_modify_host(get_host_info(host_name))
	return get_backend_core_proxy().host_execute_function(host_name, _command, *args, **kwargs)
