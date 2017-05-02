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

import os, sys, thread

import monkey
monkey.patch_all()

# tell django to read config from module tomato.config
os.environ['DJANGO_SETTINGS_MODULE']=__name__+".config"
os.environ['TOMATO_MODULE'] = "hostmanager"


import config

from lib.settings import settings


from mongoengine import connect
database_settings = settings.get_db_settings()
database_connnection = connect(database_settings['database'], host=database_settings['host'], port=database_settings['port'])
database_obj = getattr(database_connnection, database_settings['database'])


import threading, signal
_currentUser = threading.local()

def currentUser():
	return _currentUser.user if hasattr(_currentUser, "user") else None
	
def setCurrentUser(user):
	_currentUser.user = user

def login(commonName):
	if not commonName:
		return False
	user = User.objects(name=commonName).first()
	if not user:
		user = User(name=commonName)
		user.save()
	setCurrentUser(user)
	return bool(commonName)

from lib import logging
def handleError():
	import traceback
	traceback.print_exc()
	dump.dumpException()
	logging.logException()

from lib import tasks #@UnresolvedImport
scheduler = tasks.TaskScheduler(maxLateTime=30.0, minWorkers=2)

from models import *

from . import db, resources, rpcserver, firewall, dump #@UnresolvedImport
from .resources import network
from lib.cmd import fileserver, process #@UnresolvedImport
from lib.newcmd import busybox
from lib import util #@UnresolvedImport

stopped = threading.Event()

httpd_pid = None

def start():
	logging.openDefault(config.LOG_FILE)
	if not os.environ.has_key("TOMATO_NO_MIGRATE"):
		db.migrate()
	else:
		print >>sys.stderr, "Skipping migrations"
	dump.init()
	firewall.add_all_networks(network.getAll())
	global httpd_pid
	httpd_pid = busybox.httpd_start(config.TEMPLATE_DIR, config.HTTPD_PORT)
	fileserver.start()
	rpcserver.start()
	scheduler.start()

	
def reload_(*args):
	print >>sys.stderr, "Reloading..."
	logging.closeDefault()
	reload(config)
	logging.openDefault(config.LOG_FILE)

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
	if stopped.isSet() and threading.activeCount() == 1:
		return
	print >>sys.stderr, "Stopping takes long. Waiting 20 more seconds"
	stopped.wait(10)
	if stopped.isSet() and threading.activeCount() == 1:
		return
	print >>sys.stderr, "Killing process in 10 seconds..."
	stopped.wait(10)
	if stopped.isSet() and threading.activeCount() == 1:
		return
	print >>sys.stderr, "Some threads are still running:"
	_printStackTraces()
	print >>sys.stderr, "Killing process..."
	process.kill(os.getpid(), force=True)
	
def stop(*args):
	try:
		print >>sys.stderr, "Shutting down..."
		thread.start_new_thread(_stopHelper, ())
		firewall.remove_all_networks(resources.network.getAll())
		global httpd_pid
		if httpd_pid:
			busybox.httpd_stop(httpd_pid)
			httpd_pid = None
		rpcserver.stop()
		scheduler.stop()
		fileserver.stop()
		logging.closeDefault()
		stopped.set()
	except:
		import traceback
		traceback.print_exc()
		sys.exit(0)

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