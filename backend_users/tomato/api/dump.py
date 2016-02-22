from ..dump import getCount, getAll, get

def dump_count():
	"""
	returns the total number of error dumps
	"""
	return getCount()

def dump_list(after=None,list_only=False,include_data=False,compress_data=True):
	"""
	returns a list of dumps.

	Parameter *after*:
      If set, only include dumps which have a timestamp after this time.

    Parameter *list_only*:
      If True, only include dump IDs.

    Parameter *include_data*:
      If True, include detailed data. This may be about 1M per dump.

    Parameter *compress_data*:
      If True and include_data, compress the detailed data before returning. It may still be around 20M per dump after compressing.
    """
	return getAll(after=after, list_only=list_only, include_data=include_data, compress_data=compress_data)

def dump_info(dump_id, include_data=False, compress_data=True, dump_on_error=False):
	"""
	returns info of a single dump

	Parameter *dump_id*:
	  The internal id of the dump

	Parameter *include_data*:
      If True, include detailed data. This may be about 1M.

    Parameter *compress_data*:
      If True and include_data, compress the detailed data before returning. It may still be around 20M after compressing.

    Parameter *dump_on_error*:
      Set to False if you wish to create a dump if the given dump doesn't exist, i.e., this call is by the system.
	"""
	return get(dump_id, include_data=include_data, compress_data=compress_data, dump_on_error=dump_on_error)
