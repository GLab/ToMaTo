from ...lib.service import get_backend_core_proxy, is_reachable
import backend as fetching_backend
import host as fetching_host
from ...lib.settings import Config
import time


def get_all_dumpsources():
	sources = []

	try:
		host_name_list = get_backend_core_proxy().host_name_list()
	except:
		# backend_core may be restarting, especially if started simultaneously with backend_debug...
		# give it some time
		if not is_reachable(Config.TOMATO_MODULE_BACKEND_CORE):
			time.sleep(10)
			host_name_list = get_backend_core_proxy().host_name_list()
			# if this isn't solved after a second retry, raise the error...
		else:
			raise
	for h in host_name_list:
		sources.append(fetching_host.HostDumpSource(h))

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