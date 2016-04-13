from dumpsource import PullingDumpSource
from ...lib.remote_info import get_host_info

class HostDumpSource(PullingDumpSource):

	__slots__ = ("name", )

	def __init__(self, name):
		self.name = name

	def dump_source_name(self):
		return "host:%s" % self.name

	def _fetch_dumps(self, last_updatetime):
		host = get_host_info(self.name)
		if not host.exists():
			return None  # be silent in this case. it may happen that a host gets deleted ;)
		return host.get_dumps(last_updatetime)

	def _clock_offset(self):
		return get_host_info(self.name).get_clock_offset()

