from errordump import ErrorDump
from errorgroup import get_group, ErrorGroup
from ..lib.settings import settings, Config
from ..lib import util
from .. import scheduler
import fetching
import time


def insert_dump_save(dump_dict, source):
	"""
	insert dumps. afterward, shrink and save.
	"""
	group = get_group(
		dump_dict['group_id'],
		True, dump_dict['description'], source.dump_source_name()
	)
	with group.lock:
		try:
			dump_obj = ErrorDump(
				source=source.dump_source_name(),
				dumpId=dump_dict.get('dump_id', str(time.time())),
				timestamp=dump_dict.get('timestamp', None),
				description=dump_dict.get('description', None),
				type=dump_dict.get('type', None),
				softwareVersion=dump_dict.get('software_version', None),
				data=dump_dict.get("data", None)
			)
			group.insert_dump(dump_obj)
		finally:
			try:
				group.shrink()
			finally:
				group.save()
	return group

def insert_dump_unsave(dump_dict, source):
	"""
	insert dumps. do not save or shrink.
	:rtype: ErrorGroup
	"""
	group = get_group(
		dump_dict['group_id'],
		True, dump_dict['description'], source.dump_source_name()
	)
	dump_obj = ErrorDump(
		source=source.dump_source_name(),
		dumpId=dump_dict['dump_id'],
		timestamp=dump_dict['timestamp'],
		description=dump_dict['description'],
		type=dump_dict['type'],
		softwareVersion=dump_dict['software_version']
	)
	group.insert_dump(dump_obj)
	return group


def fetch_from(source_name):
	"""
	:param str source: source to fetch from
	"""
	#fixme: use insert_dump_unsave to speed up things, but handle locks...
	fetching.get_source_by_name(source_name).fetch_new_dumps(insert_dump_save)


def _get_sync_tasks():
	return {t.args[0]: tid for tid, t in scheduler.tasks.items() if t.fn == fetch_from}

def update_all():
	for source in fetching.get_all_dumpsources():
		fetch_from(source.dump_source_name())

@util.wrap_task
def scheduleUpdates():
	toSync = set([s.dump_source_name() for s in fetching.get_all_dumpsources()])
	syncTasks = _get_sync_tasks()
	syncing = set(syncTasks.keys())
	for s in toSync - syncing:
		scheduler.scheduleRepeated(settings.get_dumpmanager_config()[Config.DUMPMANAGER_COLLECTION_INTERVAL],
		                           fetch_from, s,
		                           random_offset=True)
	for s in syncing - toSync:
		scheduler.cancelTask(syncTasks[s])


def start():
	scheduler.scheduleRepeated(settings.get_dumpmanager_config()[Config.DUMPMANAGER_COLLECTION_INTERVAL],
	                           scheduleUpdates,
	                           immediate=True)

def stop():
	pass