from dumpsource import DumpSource
from ...lib.error import UserError
from ...lib.constants import DumpSourcePrefix

ACCEPTED_SOURCES = ("web", "editor")

class ApiDumpSource(DumpSource):
	"""
	This is used as dump source when receiving dumps via the backend_api API.
	It is mainly a stub to be compatible to other dumpmanager functionality.
	"""

	__slots__ = ("source_name", )

	def __init__(self, source_name):
		UserError.check(source_name in ACCEPTED_SOURCES, code=UserError.INVALID_VALUE,
		                    message="invalid dump source", data={"source_name": source_name})
		self.source_name = source_name

	def dump_source_name(self):
		return DumpSourcePrefix.API + self.source_name
