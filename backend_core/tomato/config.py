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


MAX_REQUESTS = 50

MAX_WORKERS = 25

import socket
_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_socket.connect(("8.8.8.8",80))
PUBLIC_ADDRESS = _socket.getsockname()[0]
_socket.close()

socket.setdefaulttimeout(1800)



try:
	import sys
	for path in filter(os.path.exists, ["/etc/tomato/backend.conf", os.path.expanduser("~/.tomato/backend.conf"), "backend.conf"]):
		print >> sys.stderr, "Found old-style config at %s - This is no longer supported." % (path)
except:
	import traceback
	traceback.print_exc()

