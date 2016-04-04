from ...lib.service import get_backend_core_proxy, is_reachable
import backend as fetching_backend
import host as fetching_host
from ...lib.settings import Config
import time
from ...lib.error import InternalError


def get_all_dumpsources():
	sources = []

	# step one: fetch list of all hosts' names
	host_name_list = []
	if not is_reachable(Config.TOMATO_MODULE_BACKEND_CORE):
		# backend_core may be restarting, especially if started simultaneously with backend_debug...
		# give it some time.
		time.sleep(10)
	else:
		try:
			# if this hasn't been solved by now, ignore all hosts for this fetching.
			# next time, this will be run again.
			host_name_list = get_backend_core_proxy().host_name_list()
		except Exception as exc:
			InternalError(code=InternalError.UNKNOWN, message="Failed to retrieve host list for dump fetching: %s" % exc,
			              data={"exception": repr(exc)}).dump()

	# step two: convert hosts' names into dump sources
	for h in host_name_list:
		sources.append(fetching_host.HostDumpSource(h))

	# step three: add backend modules
	for mod in Config.TOMATO_BACKEND_INTERNAL_REACHABLE_MODULES:
		sources.append(fetching_backend.BackendDumpSource(mod))

	return sources

def get_source_by_name(source_name):
	"""
	:param str source_name: source name
	"""
	if source_name.startswith("backend:"):
		return fetching_backend.BackendDumpSource(source_name[8:])
	if source_name.startswith("host:"):
		return fetching_host.HostDumpSource(source_name[5:])
	return None