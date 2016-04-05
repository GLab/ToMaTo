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

from lib import settings

tomato_module = settings.Config.TOMATO_MODULE_BACKEND_API
settings.init('/etc/tomato/config.yaml', tomato_module)
os.environ['TOMATO_MODULE'] = tomato_module

import socket
socket.setdefaulttimeout(1800)

import threading
_currentUser = threading.local()

def getCurrentUserInfo():
	"""
	get the current user's PermissionChecker object
	:return: current user's PermissionChecker object
	:rtype: authorization.PermissionChecker
	"""
	return _currentUser.user_info if hasattr(_currentUser, "user_info") else None  # fixme: _currentuser should have another name, shouldn't it?
	
def setCurrentUserInfo(user_info):
	_currentUser.user_info = user_info

def login(credentials, sslCert):
	user_info = authorization.login(*credentials) if credentials else None
	setCurrentUserInfo(user_info)
	return user_info or not credentials

from lib import logging
def handleError():
	logging.logException()
	# dump.dumpException()

from lib import tasks #@UnresolvedImport
scheduler = tasks.TaskScheduler(maxLateTime=30.0, minWorkers=5, maxWorkers=settings.settings.get_tasks_settings()[settings.Config.TASKS_MAX_WORKERS])

starttime = time.time()

from . import rpcserver
from lib.cmd import process
from lib import util, cache

stopped = threading.Event()

import dump

def start():
	logging.openDefault(settings.settings.get_log_filename())
	global starttime
	rpcserver.start()
	starttime = time.time()
	if not os.environ.has_key("TOMATO_NO_TASKS"):
		scheduler.start()
	else:
		print >>sys.stderr, "Running without tasks"
	cache.init()# this does not depend on anything (except the scheduler variable being initialized), and nothing depends on this. No need to hurry this.
	dump.init()

def reload_(*args):
	print >>sys.stderr, "Reloading..."
	logging.closeDefault()
	settings.settings.reload()
	# fixme: all cached methods should be invalidated here
	logging.openDefault(settings.settings.get_log_filename())
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
	scheduler.stop()
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

import authorization
