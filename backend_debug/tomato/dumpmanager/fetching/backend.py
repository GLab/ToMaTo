from dumpsource import PullingDumpSource
from ...lib.service import get_tomato_inner_proxy, is_reachable, is_self
from ...lib.settings import settings, Config
from ...dump import getAll
from ...lib.error import InternalError

class BackendDumpSource(PullingDumpSource):

	__slots__ = ("tomato_module", )

	def __init__(self, tomato_module):
		InternalError.check(tomato_module in Config.TOMATO_MODULES, code=InternalError.ASSERTION,
		                    message="invalid tomato module", data={"tomato_module": tomato_module})
		self.tomato_module = tomato_module

	def dump_source_name(self):
		return "backend:%s" % self.tomato_module

	def _fetch_dumps(self, last_updatetime):
		# no need to fetch if dumps are disabled...
		if not settings.get_dumpmanager_enabled(self.tomato_module):
			return None

		if is_self(self.tomato_module):
			return getAll(last_updatetime)
		else:
			if not is_reachable(self.tomato_module):
				return None  # no need to throw an exception here, just wait for the service to become reachable again.
			return get_tomato_inner_proxy(self.tomato_module).dump_list(last_updatetime)

	def _clock_offset(self):
		if is_self(self.tomato_module):
			return 0
		else:
			return 0  # fixme: measure for remote backend services

