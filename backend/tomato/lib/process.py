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

import util, exceptions

def killPidfile(host, pidfile):
	host.execute("[ -f \"%(pidfile)s\" ] && (cat \"%(pidfile)s\" | xargs -r kill; true) && rm \"%(pidfile)s\"; true" % {"pidfile": pidfile})

def killPortUser(host, port):
	assert port
	host.execute("for i in $(lsof -i:%d -t); do cat /proc/$i/status | fgrep PPid | cut -f2; done | xargs -r kill" % port)
	host.execute("lsof -i:%d -t | xargs -r kill" % port)

def portFree(host, port):
	try:
		res = host.execute("lsof -i:%d -t" % port)
		return len(res.splitlines()) == 0 
	except exceptions.CommandError:
		return True

def processRunning(host, pidfile, name=""):
	cmdline = util.lines(host.execute("[ -f \"%(pidfile)s\" ] && (cat \"%(pidfile)s\" | xargs -r ps --no-headers --format cmd --pid); true" % {"pidfile": pidfile}))
	if not len(cmdline):
		return False
	if name:
		return name in cmdline[0]
		