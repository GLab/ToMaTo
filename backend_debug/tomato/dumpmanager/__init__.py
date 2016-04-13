from errordump import ErrorDump
from errorgroup import get_group, ErrorGroup
from ..lib.settings import settings, Config
from ..lib import util
from .. import scheduler
import fetching


def insert_dump(dump_dict, source):
	"""
	insert dumps. afterward, shrink and save.
	"""
	group = get_group(
		dump_dict['group_id'],
		True, dump_dict['description'], source.dump_source_name()
	)
	with group.lock:
		try:
			dump_obj = ErrorDump.from_dict(dump_dict, source)
			if dump_obj.timestamp >= source.get_last_updatetime():
				group.insert_dump(dump_obj)
		finally:
			try:
				group.shrink()
			finally:
				group.save()


def fetch_from(source_name):
	"""
	:param str source: source to fetch from
	"""
	fetching.get_source_by_name(source_name).fetch_new_dumps(insert_dump)

def list_all_dumpsource_names():
	return [s.dump_source_name() for s in fetching.get_all_dumpsources()]


def _get_sync_tasks():
	return {t.args[0]: tid for tid, t in scheduler.tasks.items() if t.fn == fetch_from}

def update_all():
	for source in fetching.get_all_dumpsources():
		source.fetch_new_dumps(insert_dump)

def start():
	scheduler.scheduleMaintenance(settings.get_dumpmanager_config()[Config.DUMPMANAGER_COLLECTION_INTERVAL],
	                              list_all_dumpsource_names, fetch_from)

def stop():
	pass