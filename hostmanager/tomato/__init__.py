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

import os, sys, atexit

# tell django to read config from module tomato.config
os.environ['DJANGO_SETTINGS_MODULE']="tomato.config"

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
	if not sslCert:
		return False
	setCurrentUser(sslCert.get_subject().commonName)
	return bool(sslCert)


from models import *
	
if not config.MAINTENANCE:
	db_migrate()

import api

from tomato import lib, resources, accounting #@UnresolvedImport

from rpcserver import start as startRPCserver
from rpcserver import stop as stopRPCserver
from lib.cmd.fileserver import start as startFileserver #@UnresolvedImport
from lib.cmd.fileserver import stop as stopFileserver #@UnresolvedImport
from lib.cmd import bittorrent #@UnresolvedImport
from lib import logging #@UnresolvedImport

if not config.MAINTENANCE:
	logging.openDefault(config.LOG_FILE)
	atexit.register(logging.closeDefault)
	resources.init()
	accounting.task.start() #@UndefinedVariable
	bittorrent.startClient(config.TEMPLATE_DIR)
	
