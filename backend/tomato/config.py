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

AUTH = []

SSH_KEY = os.path.expanduser('~/.ssh/id_rsa')

PASSWORD_SALT = "tomato"

TIMEOUTS = {
	"STOP": 4,
	"DESTROY": 12,
	"REMOVE": 24,
}

TIMEOUT_WARNING = 7 #days

LOGIN_TIMEOUT = 1

SERVER = [
	{
		"PORT": 8000,
		"SSL": False,
		"SSL_OPTS": {
			"private_key" : "",
			"ca_key": ""
		}
	}
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite'
    }
}

TEMPLATE_HOSTSERVER = None

LOCAL_TMP_DIR = "/tmp/tomato"
LOG_DIR = "logs"

REMOTE_DIR = "/root/tomato"

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'

INSTALLED_APPS = ('tomato', 'south')

MAINTENANCE = os.environ.has_key('TOMATO_MAINTENANCE')

ERROR_NOTIFY = []

MAIL = {
	'SUBJECT_PREFIX': "[ToMaTo] ",
	'SUBJECT_SUFFIX': "",
	'BODY_PREFIX': "Dear %s,\n\n",
	'BODY_SUFFIX': "\n\nSincerely,\n   your ToMaTo backend\n\n[This mail has been created automatically, please do not reply]",
	'SENDER_NAME': "ToMaTo Backend",
	'SENDER_MAIL': "support@german-lab.de",
	'SERVER': "localhost",
}

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
