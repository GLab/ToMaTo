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
os.environ['DJANGO_SETTINGS_MODULE']="tomato.config"


# This is the main tomato api file. All access to tomato must use the following 
# methods. Direct import and usage of other classes of tomato is strongly 
# discouraged as it is likely to break tomato.
#
# Note: since xml-rpc does not support None values all methods must return 
# something and all return values must not contain None.

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
	
if not config.MAINTENANCE:
	db_migrate()

from auth import login #@UnresolvedImport, pylint: disable-msg=E0611

import api