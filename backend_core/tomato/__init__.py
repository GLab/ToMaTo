# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import os, sys, signal, time, thread

import monkey
monkey.patch_all()

from lib import settings

tomato_module = settings.Config.TOMATO_MODULE_BACKEND_CORE
settings.init('/etc/tomato/config.yaml', tomato_module)
os.environ['TOMATO_MODULE'] = tomato_module

import socket
socket.setdefaulttimeout(1800)

from mongoengine import connect
database_settings = settings.settings.get_db_settings()
database_connnection = connect(database_settings['database'], host=database_settings['host'], port=database_settings['port'])
database_obj = getattr(database_connnection, database_settings['database'])

def db_migrate():
	def getMigration(version):
		try:
			return __import__("tomato.migrations.migration_%04d" % version, {}, {}, 'migration_%04d' % version).migrate
		except ImportError:
			return None

	from .db import data
	version = data.get('db_version', 0)
	print >>sys.stderr, "Database version: %04d" % version
	if version > 0 and not getMigration(version):
		raise Exception("Database is newer than code")
	if not version and not getMigration(1):
		raise Exception("Failed to migrate to initial version")
	while True:
		version += 1
		migrate = getMigration(version)
		if not migrate:
			break
		print >>sys.stderr, " - migrating to version %04d..." % version
		try:
			migrate()
		except:
			import traceback
			traceback.print_exc()
			raise
		data.set('db_version', version)

import threading
_currentUser = threading.local()

def currentUser():
	return _currentUser.user if hasattr(_currentUser, "user") else None  # fixme
	
def setCurrentUser(user):
	_currentUser.user = user

def login(credentials, sslCert):
	user = auth.login(*credentials) if credentials else None
	setCurrentUser(user)
	return user or not credentials

from lib import logging
def handleError():
	logging.logException()
	dump.dumpException()

from lib import tasks #@UnresolvedImport
scheduler = tasks.TaskScheduler(maxLateTime=30.0, minWorkers=5, maxWorkers=settings.settings.get_tasks_settings()[settings.Config.TASKS_MAX_WORKERS])

starttime = time.time()

from . import host, auth, rpcserver #@UnresolvedImport
from lib.cmd import bittorrent, process #@UnresolvedImport
from lib import util, cache #@UnresolvedImport

scheduler.scheduleRepeated(settings.settings.get_bittorrent_settings()['bittorrent-restart'], util.wrap_task(bittorrent.restartClient))

stopped = threading.Event()

import dump
import dumpmanager
import models

def start():
	logging.openDefault(settings.settings.get_log_filename())
	if not os.environ.has_key("TOMATO_NO_MIGRATE"):
		db_migrate()
	else:
		print >>sys.stderr, "Skipping migrations"
	auth.init()
	global starttime
	bittorrent.startTracker(settings.settings.get_bittorrent_settings()['tracker-port'], settings.settings.get_template_dir())
	bittorrent.startClient(settings.settings.get_template_dir())
	rpcserver.start()
	starttime = time.time()
	if not os.environ.has_key("TOMATO_NO_TASKS"):
		scheduler.start()
	else:
		print >>sys.stderr, "Running without tasks"
	dump.init()
	dumpmanager.init()# important: must be called after dump.init()
	cache.init()# this does not depend on anything (except the scheduler variable being initialized), and nothing depends on this. No need to hurry this.
	
def reload_(*args):
	print >>sys.stderr, "Reloading..."
	logging.closeDefault()
	settings.settings.reload()
	# fixme: all cached methods should be invalidated here
	logging.openDefault(settings.settings.get_log_filename())
	dumpmanager.rebuild_dump_source_list()
	#stopRPCserver()
	#startRPCserver()

def _printStackTraces():
	import traceback
	for threadId, stack in sys._current_frames().items():
		print >>sys.stderr, "ThreadID: %s" % threadId
		for filename, lineno, name, line in traceback.extract_stack(stack):
			print >>sys.stderr, '\tFile: "%s", line %d, in %s' % (filename, lineno, name)
			if line:
				print >>sys.stderr, "\t\t%s" % (line.strip())
	

def _stopHelper():
	stopped.wait(10)
	if stopped.isSet():
		return
	print >>sys.stderr, "Stopping takes long, waiting some more time..."
	stopped.wait(10)
	if stopped.isSet():
		return
	print >>sys.stderr, "Ok last chance, killing process in 10 seconds..."
	stopped.wait(10)
	if stopped.isSet():
		return
	print >>sys.stderr, "Some threads are still running:"
	_printStackTraces()
	print >>sys.stderr, "Killing process..."
	process.kill(os.getpid(), force=True)

def stop(*args):
	print >>sys.stderr, "Shutting down..."
	thread.start_new_thread(_stopHelper, ())
	rpcserver.stop()
	host.stopCaching()
	scheduler.stop()
	bittorrent.stopTracker()
	bittorrent.stopClient()
	logging.closeDefault()
	stopped.set()

def run():
	start()
	signal.signal(signal.SIGTERM, stop)
	signal.signal(signal.SIGINT, stop)
	signal.signal(signal.SIGHUP, reload_)
	try:
		while not stopped.isSet():
			stopped.wait(1.0)
	except KeyboardInterrupt:
		stop()