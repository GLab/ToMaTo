from ..dump import getAll

def dump_list(after=None):
	"""
	returns a list of dumps.

	Parameter *after*:
		If set, only include dumps which have a timestamp after this time.
	"""
	return getAll(after=after)
