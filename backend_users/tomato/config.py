# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2016 Dennis Schwerdel, University of Kaiserslautern
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

SERVER_PORT = 8000
SERVER_CERT = "/etc/tomato/service.pem"
SERVER_CA_CERTS = "/etc/tomato/ca.pem"

DATABASE = 'tomato_users'
DATABASE_HOST = 'localhost'
if "DB_PORT_27017_TCP" in os.environ:
	DATABASE_HOST = 'mongodb://%s:%s/%s' % (os.getenv('DB_PORT_27017_TCP_ADDR'), os.getenv('DB_PORT_27017_TCP_PORT'), DATABASE)

RPC_TIMEOUT = 60

EMAIL_SMTP = "localhost"
EMAIL_FROM = "ToMaTo backend <tomato@localhost>"
EMAIL_SUBJECT_TEMPLATE = "[ToMaTo] %(subject)s"
EMAIL_MESSAGE_TEMPLATE = "Dear %(realname)s,\n\n%(message)s\n\n\nSincerely,\n  your ToMaTo backend"

DEFAULT_QUOTA = {
	"cputime": 5.0 *(60*60*24*30), # 5 cores all the time
	"memory": 10e9, # 10 Gb all the time
	"diskspace": 100e9, # 100 Gb all the time
	"traffic": 5.0e6 /8.0*(60*60*24*30), # 5 Mbit/s all the time
	"continous_factor": 1.0
}

MAX_REQUESTS = 50

MAX_WORKERS = 25

import socket
socket.setdefaulttimeout(300)

# E-Mail sent to new users after registering
NEW_USER_WELCOME_MESSAGE = {
'subject': "Registration at ToMaTo-Lab",
'body': "Dear %s,\n\n\
Welcome to the ToMaTo-Lab testbed. Your registration will be reviewed by our administrators shortly. Until then, you can create a topology (but not start it).\n\
You should also subscribe to our mailing list at https://lists.uni-kl.de/tomato-lab.\n\n\
Best Wishes,\nThe ToMaTo Testbed"
}

# E-Mail sent to administrators when a new user registers
NEW_USER_ADMIN_INFORM_MESSAGE = {
'subject': "User Registration",
'body': "Dear ToMaTo administrator,\n\n\
A new user, %s, has just registered at the ToMaTo testbed.\n\
You can review all pending user registrations at https://master.tomato-lab.org/account/registrations\n\n\
Best Wishes,\nThe ToMaTo Testbed"
}

try:
	import sys
	for path in filter(os.path.exists, ["/etc/tomato/backend_users.conf", os.path.expanduser("~/.tomato/backend_users.conf"), "backend_users.conf"]):
		try:
			execfile(path)
			print >>sys.stderr, "Loaded config from %s" % path
		except Exception, exc:
			print >>sys.stderr, "Failed to load config from %s: %s" % (path, exc)
except:
	import traceback
	traceback.print_exc()