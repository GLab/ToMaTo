"""
this contains abstract dump source classes.
"""
import time
from ...lib.error import Error, InternalError, TransportError
from ...lib.exceptionhandling import on_error_continue, wrap_and_handle_current_exception
from ...db import data

DB_FORMAT = "dumpsource:%s/last_updatetime"

class DumpSource(object):
	"""
	A source of dumps.
	"""

	__slots__ = ()

	def dump_source_name(self):
		"""
		used as data in dumps.
		:return: unique dump source name.
		:rtype: str
		"""
		raise NotImplementedError()

	def get_last_updatetime(self):
		"""
		get the last update time for this source.
		:return:
		"""
		return data.get(DB_FORMAT % self.dump_source_name(), 0)

	def _set_last_updatetime(self, last_updatetime):
		"""
		set the last update time for this source.
		:param last_updatetime:
		:return:
		"""
		data.set(DB_FORMAT % self.dump_source_name(), last_updatetime)



class PullingDumpSource(DumpSource):
	"""
	A DumpSource where the dumpmanager must pull dumps itself.
	"""

	__slots__ = ()

	def _fetch_dumps(self, last_updatetime):
		"""
		fetch dumps from the source after the given timestamp.
		:param float last_updatetime: last update time. timestamp should be put as seen by the remote.
		:return: a list of dump dicts. Return None if fetching is currently not possible.
		:rtype: list(dict) or None
		"""
		raise NotImplementedError()

	def _clock_offset(self):
		"""
		get clock offset.
		:return: clock offset
		:rtype: float
		"""
		raise NotImplementedError()

	@on_error_continue()
	def fetch_new_dumps(self, insert_dump_func):
		"""
		refresh dumps
		for each dump: call insert_dump_func(dump_dict, self)
		:param func insert_dump_func: function to insert dumps
		:return: None
		:rtype: None
		"""
		offset = self._clock_offset()
		if offset is None:
			return  # if this is unavailable, something really strange is happening on backend_core. Let's not fetch for now.
							# probably, this is simply because backend_core hasn't received any host info yet.


		this_fetch_time = time.time() - offset

		fetch_results = self._fetch_dumps(self.get_last_updatetime())
		if fetch_results is None:
			return  # this means that fetching is currently not possible.

		for dump_dict in fetch_results:
			try:
				insert_dump_func(dump_dict, self)
			except:
				wrap_and_handle_current_exception(re_raise=False)

		self._set_last_updatetime(this_fetch_time)
