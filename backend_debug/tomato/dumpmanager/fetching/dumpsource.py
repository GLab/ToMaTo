import time
from ...lib.error import Error, InternalError, TransportError
from ...lib.exceptionhandling import on_error_continue, wrap_and_handle_current_exception
from ...db import data

class DumpSource(object):

	__slots__ = ()

	def dump_source_name(self):
		raise NotImplemented()



class PullingDumpSource(DumpSource):

	__slots__ = ()

	def _fetch_dumps(self, last_updatetime):
		"""
		fetch dumps from the source after the given timestamp.
		:param float last_updatetime: last update time. timestamp should be put as seen by the remote.
		:return: a list of dump dicts. Return None if fetching is currently not possible.
		:rtype: list(dict) or None
		"""
		raise NotImplemented()

	def _clock_offset(self):
		raise NotImplemented()

	def get_last_updatetime(self):
		return data.get("dumpsource:%s/last_updatetime" % self.dump_source_name(), 0)

	def _set_last_updatetime(self, last_updatetime):
		data.set("dumpsource:%s/last_updatetime" % self.dump_source_name(), last_updatetime)

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
