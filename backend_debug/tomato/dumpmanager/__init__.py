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
	#fixme: use insert_dump_unsave to speed up things, but handle locks...
	fetching.get_source_by_name(source_name).fetch_new_dumps(insert_dump)


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