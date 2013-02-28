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

import os, sys

# tell django to read config from module tomato.config
os.environ['DJANGO_SETTINGS_MODULE']=__name__+".config"

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

	
import threading, signal
_currentUser = threading.local()

def currentUser():
	return _currentUser.user if hasattr(_currentUser, "user") else None
	
def setCurrentUser(user):
	_currentUser.user = user

def login(credentials, sslCert):
	if not sslCert:
		return False
	setCurrentUser(sslCert.get_subject().commonName)
	return bool(sslCert)


from models import *
	
import api

from . import lib, resources, accounting, rpcserver, elements #@UnresolvedImport
from lib.cmd import bittorrent, fileserver, process #@UnresolvedImport
from lib import logging #@UnresolvedImport

_btClient = None

stopped = threading.Event()

def start():
	logging.openDefault(config.LOG_FILE)
	db_migrate()
	resources.init()
	accounting.task.start() #@UndefinedVariable
	global _btTracker, _btClient
	_btClient = bittorrent.startClient(config.TEMPLATE_DIR)
	fileserver.start()
	rpcserver.start()
	elements.timeoutTask.start() #@UndefinedVariable
	
def reload_(*args):
	print >>sys.stderr, "Reloading..."
	logging.closeDefault()
	reload(config)
	logging.openDefault(config.LOG_FILE)

def stop(*args):
	try:
		print >>sys.stderr, "Shutting down..."
		rpcserver.stop()
		fileserver.stop()
		elements.timeoutTask.stop() #@UndefinedVariable
		accounting.task.stop() #@UndefinedVariable
		process.kill(_btClient)
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