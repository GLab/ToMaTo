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

import os

CERTIFICATE = "/etc/tomato/backend.pem"
EXTERNAL_URLS = {
				'aup':  "http://tomato-lab.org/aup",
				'help': "https://github.com/GLab/ToMaTo/wiki",
				'impressum': "http://tomato-lab.org/contact/",
				'project': "http://tomato-lab.org",
				'news_feed': "http://www.tomato-lab.org/feed.json"
				}

TEMPLATE_PATH = "/var/lib/tomato/templates"
TRACKER_PORT = 8002
BITTORRENT_RESTART = 60 * 30

AUTH = []

AUTH.append ({
	"name": "",
	"provider": "internal",
	"options": {
			"password_timeout": None,
			"account_timeout": 60*60*24*365*5, # 5 years
			"allow_registration": True,
			"default_flags": ["over_quota", "new_account"]
	}
})

LOG_FILE = "/var/log/tomato/main.log"

SERVER = []

SERVER.append({
	"PORT": 8000,
	"SSL": True,
	"SSL_OPTS": {
		"cert_file" : "/etc/tomato/server.cert",
		"key_file": "/etc/tomato/server.cert",
	}
})

SERVER.append({
	"PORT": 8001,
	"SSL": False
})

DATABASES = {}

DATABASES['default'] = {
	'ENGINE': 'django.db.backends.postgresql_psycopg2',
	'NAME': 'tomato'
}

HOST_UPDATE_INTERVAL = 60
HOST_AVAILABILITY_HALFTIME = 60.0 * 60 * 24 * 90 # 90 days 
RESOURCES_SYNC_INTERVAL = 600

EMAIL_FROM = "ToMaTo backend <tomato@localhost>"
EMAIL_SUBJECT_TEMPLATE = "[ToMaTo] %(subject)s"
EMAIL_MESSAGE_TEMPLATE = "Dear %(realname)s,\n\n%(message)s\n\n\nSincerely,\n  your ToMaTo backend"

# Django mail config
#EMAIL_HOST = ""
#EMAIL_PORT =
#EMAIL_HOST_USER =
#EMAIL_HOST_PASSWORD =
#EMAIL_USE_TLS

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'en-us'

INSTALLED_APPS = ('tomato', 'south')
SECRET_KEY = 'not needed'

DISABLE_TRANSACTION_MANAGEMENT = True

MAINTENANCE = os.environ.has_key('TOMATO_MAINTENANCE')

ERROR_NOTIFY = []

import socket
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
	
import math
HOST_AVAILABILITY_FACTOR = math.pow(0.5, HOST_UPDATE_INTERVAL/HOST_AVAILABILITY_HALFTIME)
