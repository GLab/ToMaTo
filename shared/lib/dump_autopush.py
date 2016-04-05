from service import get_backend_debug_proxy
from settings import settings, Config
import dump as dump_lib
import threading
import thread
import time

auto_push = False
must_autopush = threading.Event()


def on_dump_create():
	must_autopush.set()

def dump_pusher():
	# there must be one thread running this.
	# this thread is started in init()
	while auto_push:
		time.sleep(5)  # avoid flooding: only one dump per 5 seconds via push!
		try:
			with dump_lib.dumps_lock:
				if len(dump_lib.dumps) > 0:
					# get dump_id with smallest timestamp
					dump_id = sorted(dump_lib.dumps.iteritems(), key=lambda d: d[1]['timestamp'])[0][0]

					# push to backend_debug
					get_backend_debug_proxy().dump_push_from_backend(
						settings.get_tomato_module_name(),
						dump_lib.load_dump(dump_id, load_data=True))

					# remove from list
					dump_lib.remove_dump(dump_id)
				else:
					must_autopush.clear()
		except:
			must_autopush.clear()  # wait for next round if an error occurred.
		must_autopush.wait()


def init():
	global auto_push
	auto_push = settings.get_dump_config()[Config.DUMPS_AUTO_PUSH]
	if auto_push:
		dump_lib.on_dump_create = on_dump_create
		thread.start_new_thread(dump_pusher, ())
		from .. import scheduler
		scheduler.scheduleRepeated(settings.get_dumpmanager_config()[Config.DUMPMANAGER_COLLECTION_INTERVAL], on_dump_create, immediate=True)
