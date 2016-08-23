from dumpsource import DumpSource
from ...lib.service import get_tomato_inner_proxy, is_reachable, is_self
from ...lib.settings import settings, Config
from ...dump import getAll
from ...lib.error import InternalError, UserError

ACCEPTED_SOURCES = ("web", "editor")

class ApiDumpSource(DumpSource):

	__slots__ = ("source_name", )

	def __init__(self, source_name):
		UserError.check(source_name in ACCEPTED_SOURCES, code=UserError.INVALID_VALUE,
		                    message="invalid dump source", data={"source_name": source_name})
		self.source_name = source_name

	def dump_source_name(self):
		return "api:%s" % self.source_name
