from .lib.settings import Config
from .lib.error import UserError
from .lib.userflags import Flags
from .lib.service import is_reachable, get_tomato_inner_proxy, is_self, get_backend_users_proxy
from . import scheduler
from threading import RLock, Thread

class ModuleStatus(object):
	__slots__ = ("tomato_module", "lock",
	             "last_problems",
	             "last_reachable")

	def __init__(self, tomato_module):
		self.tomato_module = tomato_module
		self.last_problems = set()
		self.last_reachable = True
		self.lock = RLock()

	def send_problem_report(self, problem, resolved=False):
		title = "Backend Problems: %s" % self.tomato_module
		if resolved:
			message = "A problem on %s has been resolved: %s" % (self.tomato_module, problem)
		else:
			message = "A problem on %s has been detected: %s" % (self.tomato_module, problem)
		get_backend_users_proxy().broadcast_message_multifilter(title=title, message=message, ref=None, subject_group="backend failure",
																			filters = [
																				(None, Flags.GlobalHostManager),
																				(None, Flags.GlobalHostContact),
																				(None, Flags.Debug)
																			])

	def check(self):
		with self.lock:
			if is_reachable(self.tomato_module) or is_self(self.tomato_module):
				if is_self(self.tomato_module):
					from .api.debug import _debug_stats_withoutauth
					debug_stats = _debug_stats_withoutauth()
				else:
					api = get_tomato_inner_proxy(self.tomato_module)
					if not self.last_reachable:
						self.last_reachable = True
						self.send_problem_report("service unreachable", True)
					debug_stats = api.debug_stats()
				new_problems = set(debug_stats.get("problems", ()))
				for new_problem in (new_problems-self.last_problems):
					self.send_problem_report(new_problem, False)
				for resolved_problem in (self.last_problems-new_problems):
					self.send_problem_report(resolved_problem, True)
				self.last_problems = new_problems
			else:
				if self.last_reachable:
					self.send_problem_report("service unreachable", False)
					self.last_reachable = False

	def get_problems(self):
		res = []
		with self.lock:
			self.check()
			if not self.last_reachable:
				res.append("service unreachable")
			res.extend(self.last_problems)
			return res

	def info(self):
		with self.lock:
			self.check()
			return {
				'reachable': self.last_reachable,
				'problems': self.get_problems()
			}






modules = {}
for tomato_module in Config.TOMATO_BACKEND_MODULES:
	modules[tomato_module] = ModuleStatus(tomato_module)
def _get_module(tomato_module):
	"""
	:param str tomato_module:
	:return:
	:rtype: ModuleStatus
	"""
	UserError.check(tomato_module in Config.TOMATO_BACKEND_MODULES, code=UserError.INVALID_VALUE, message="no such backend module", data={"tomato_module": tomato_module})
	return modules[tomato_module]

def get_all_stats():
	return {tomato_module: _get_module(tomato_module).info() for tomato_module in Config.TOMATO_BACKEND_MODULES}


def checkModule(tomato_module):
	_get_module(tomato_module).check()

def schedule_maintenance():
	import time
	time.sleep(30)
	for tomato_module in Config.TOMATO_BACKEND_MODULES:
		is_not_accounting = tomato_module!=Config.TOMATO_MODULE_BACKEND_ACCOUNTING
		scheduler.scheduleRepeated(5*60, checkModule, tomato_module, immediate=is_not_accounting, random_offset=is_not_accounting)
Thread(target=schedule_maintenance).start()
