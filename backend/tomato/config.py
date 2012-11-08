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

import os, socket

VERSION = 0.1

CERTIFICATE = "../cli/admin.pem"

TEMPLATE_PATH = "templates"
TRACKER_PORT = 8001

AUTH = [
	{
		"name": "",
		"provider": "internal",
		"options": {
				"password_timeout": None,
				"account_timeout": 60*60*24*365*5, # 5 years
				"allow_registration": True,
				"default_flags": ["over_quota"]
		}
	},
	{
		"name": "guest",
		"provider": "dict",
		"options": {
				"users": {
						"guest": "guest"
				},
				"flags": ["no_topology_create", "over_quota"],
				"hash": None
		}
	}
]

LOG_FILE = "main.log"

SERVER = [
	{
		"PORT": 8000,
		"SSL": False,
		"SSL_OPTS": {
			"cert_file" : "/etc/tomato/server.cert",
			"key_file": "/etc/tomato/server.cert",
		}
	}
]

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': 'db.sqlite'
	}
}

HOST_UPDATE_INTERVAL = 60
RESOURCES_SYNC_INTERVAL = 600

MAIL = {}

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'

INSTALLED_APPS = ('tomato', 'south')

DISABLE_TRANSACTION_MANAGEMENT = True

MAINTENANCE = os.environ.has_key('TOMATO_MAINTENANCE')

ERROR_NOTIFY = []

_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_socket.connect(("8.8.8.8",80))
PUBLIC_ADDRESS = _socket.getsockname()[0]
_socket.close()

try:
	import sys
	for path in filter(os.path.exists, ["/etc/tomato/backend.conf", os.path.expanduser("~/.tomato/backend.conf"), "backend.conf"]):
		try:
			execfile(path)
			print >>sys.stderr, "Loaded config from %s" % path
		except Exception, exc:
			print >>sys.stderr, "Failed to load config from %s: %s" % (path, exc)
except:
	import traceback
	traceback.print_exc()

if not isinstance(SERVER, list):
	SERVER = [SERVER]
