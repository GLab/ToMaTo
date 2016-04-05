from ..dumpmanager import insert_dump
from ..dumpmanager.fetching.backend import BackendDumpSource

def dump_push_from_backend(tomato_module, dump_dict):
	"""
	actively push a dump to the dumpmanager.
	Only call this as a backend service.
	"""
	source = BackendDumpSource(tomato_module)
	insert_dump(dump_dict, source)