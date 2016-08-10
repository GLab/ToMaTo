from ..dumpmanager import insert_dump
from ..dumpmanager.fetching.api import ApiDumpSource
from ..dumpmanager.fetching.backend import BackendDumpSource
from ..lib.error import UserError

def dump_push_from_backend(tomato_module, dump_dict):
	"""
	actively push a dump to the dumpmanager.
	Only call this as a backend service.
	"""
	source = BackendDumpSource(tomato_module)
	insert_dump(dump_dict, source)

def receive_dump_from_api(source_name, dump_dict):
	"""
	receive a dump from the api
	"""
	# verify dump_dict correctness
	for k in ("dump_id", "group_id",
	          "description", "timestamp"):
		UserError.check(k in dump_dict, code=UserError.INVALID_DATA, message="dump_dict is missing a key", data={"key_missing": k})

	# insert dump
	source = ApiDumpSource(source_name)
	insert_dump(dump_dict, source)
