import os
import psutil
from .lib.settings import settings, Config
from .lib.service import get_backend_debug_proxy
from . import scheduler

def service_status():
	# file system
	fs_stats = os.statvfs("/")
	fs_bytes_avail = fs_stats.f_frsize*fs_stats.f_bavail
	fs_bytes_total = fs_stats.f_frsize*fs_stats.f_blocks

	#memory
	mem_stats = psutil.virtual_memory()
	mem_avail = mem_stats.available
	mem_total = mem_stats.total

	return {
		"filesystem": {
			"avail": fs_bytes_avail/(1024*1024),
			"total": fs_bytes_total/(1024*1024)
		},
		"memory": {
			"avail": mem_avail/(1024*1024),
			"total": mem_total/(1024*1024)
		}
	}


def problems():
	res = []

	mem_stats = psutil.virtual_memory()
	free_mem_percent = 1-mem_stats.percent
	if free_mem_percent < 0.06:
		res.append("memory usage is critical")

	fs_stats = os.statvfs("/")
	free_fs_percent = float(fs_stats.f_bavail) / float(fs_stats.f_blocks)
	if free_fs_percent < 0.06:
		res.append("disk usage is critical")

	return res