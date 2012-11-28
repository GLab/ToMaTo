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

import os, sys, signal, time

# tell django to read config from module tomato.config
os.environ['DJANGO_SETTINGS_MODULE']=__name__+".config"

#TODO: debian package
#TODO: tinc clustering
#TODO: external network management
#TODO: interface auto-config
#TODO: topology timeout
#TODO: link measurement

def db_migrate():
	"""
	NOT CALLABLE VIA XML-RPC
	Migrates the database forward to the current structure using migrations
	from the package tomato.migrations.
	"""
	from django.core.management import call_command
	call_command('syncdb', verbosity=0)
	from south.management.commands import migrate
	cmd = migrate.Command()
	cmd.handle(app="tomato", verbosity=1)


import config

	
import threading
_currentUser = threading.local()

def currentUser():
	return _currentUser.user if hasattr(_currentUser, "user") else None
	
def setCurrentUser(user):
	_currentUser.user = user

def login(credentials, sslCert):
	user = auth.login(*credentials)
	setCurrentUser(user)
	return user

starttime = None

from models import *
	
import api

from . import lib, resources, host, accounting, auth, rpcserver #@UnresolvedImport
from lib.cmd import bittorrent, process #@UnresolvedImport
from lib import logging #@UnresolvedImport

_btTracker = None
_btClient = None

stopped = threading.Event()

def start():
	logging.openDefault(config.LOG_FILE)
	db_migrate()
	auth.init()
	resources.init()
	host.task.start() #@UndefinedVariable
	accounting.task.start() #@UndefinedVariable
	auth.task.start() #@UndefinedVariable
	global _btTracker, _btClient, starttime
	_btTracker = bittorrent.startTracker(config.TRACKER_PORT, config.TEMPLATE_PATH)
	_btClient = bittorrent.startClient(config.TEMPLATE_PATH)
	rpcserver.start()
	starttime = time.time()
	
def reload_(*args):
	print >>sys.stderr, "Reloading..."
	logging.closeDefault()
	reload(config)
	logging.openDefault(config.LOG_FILE)
	#stopRPCserver()
	#startRPCserver()

def forceStop(*args):
	print >>sys.stderr, "Force stopping..."
	sys.exit(1)

def stop(*args):
	print >>sys.stderr, "Shutting down..."
	signal.alarm(30)
	signal.signal(signal.SIGALRM, forceStop)
	rpcserver.stop()
	auth.task.stop() #@UndefinedVariable
	host.task.stop() #@UndefinedVariable
	accounting.task.stop() #@UndefinedVariable
	process.kill(_btTracker)
	process.kill(_btClient)
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