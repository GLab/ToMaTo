from ..lib.error import UserError
from .. import scheduler
import traceback, sys
from api_helpers import getCurrentUserInfo
from ..lib.debug import run
from ..lib.settings import Config
from ..service_status import service_status, problems
from ..service_status_manager import get_all_stats
from ..lib.service import is_reachable, is_self, get_tomato_inner_proxy, get_backend_core_proxy
from ..lib.remote_info import get_host_info
from ..lib.exceptionhandling import wrap_and_handle_current_exception
from ..lib.error import InternalError

def ping():
	return True

def _debug_stats_withoutauth():
	"""
	debug stats, but without authentication. Only use internally.
	:return:
	"""
	return {
		"scheduler": scheduler.info(),
		"threads": map(traceback.extract_stack, sys._current_frames().values()),
		"system": service_status(),
		"problems": problems()
	}

def debug_stats(tomato_module=Config.TOMATO_MODULE_BACKEND_API):
	getCurrentUserInfo().check_may_view_debugging_info()
	if is_self(tomato_module):
		return _debug_stats_withoutauth()
	else:
		api = get_tomato_inner_proxy(tomato_module)
		return api.debug_stats()

def debug_services_overview():
	return get_all_stats()

def debug_services_reachable():
	res = {module: is_reachable(module) for module in Config.TOMATO_BACKEND_MODULES}
	res[Config.TOMATO_MODULE_BACKEND_API] = True
	return res



def debug_debug_internal_api_call(_tomato_module, _command, args=None, kwargs=None, profile=True):
	"""
	debug an internal API call
	use lib.debug.DebugResult.unmarshal on the result to get more functionality
	:param _tomato_module:
	:param _command:
	:param args:
	:param kwargs:
	:param profile:
	:return:
	"""
	getCurrentUserInfo().check_may_view_debugging_info()
	if is_self(_tomato_module):
		from .. import api
		func = getattr(api, _command)
		result = run(func, args, kwargs, profile)
		return result.marshal()
	else:
		return get_tomato_inner_proxy(_tomato_module).debug_debug_internal_api_call(_command, args=None, kwargs=None, profile=True)


def debug_run_internal_api_call(_tomato_module, _command, *args, **kwargs):
	getCurrentUserInfo().check_allow_active_debugging()
	return get_tomato_inner_proxy(_tomato_module)._call(_command, args, kwargs)

def debug_run_host_api_call(host_name, _command, *args, **kwargs):
	getCurrentUserInfo().check_allow_active_debugging()
	getCurrentUserInfo().check_may_modify_host(get_host_info(host_name))
	return get_backend_core_proxy().host_execute_function(host_name, _command, *args, **kwargs)


def debug_execute_task(tomato_module, task_id):
	getCurrentUserInfo().check_may_execute_tasks()
	if is_self(tomato_module):
		return scheduler.executeTask(task_id, force=True)
	else:
		get_tomato_inner_proxy(tomato_module).debug_execute_task(task_id)

def debug_throw_error(tomato_module=None, data=None):
	"""
	throw an error that is then dumped.
	:return:
	"""
	getCurrentUserInfo().check_allow_active_debugging()
	if tomato_module is None:
		tomato_module = Config.TOMATO_MODULE_BACKEND_API
	UserError.check(tomato_module != Config.TOMATO_MODULE_BACKEND_ACCOUNTING, code=UserError.INVALID_VALUE, message="backend_accounting does not support dumps")
	UserError.check(tomato_module in Config.TOMATO_BACKEND_MODULES, code=UserError.INVALID_VALUE, message="bad tomato module", data={"tomato_module": tomato_module})
	if is_self(tomato_module):
		try:
			InternalError.check(False, code=InternalError.UNKNOWN, message="Test Dump", todump=True, data=data)
		except:
			wrap_and_handle_current_exception(re_raise=True)
	else:
		get_tomato_inner_proxy(tomato_module).debug_throw_error(data=data)
