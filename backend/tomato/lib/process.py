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

def killPidfile(host, pidfile, force=False):
	host.execute("[ -f %(pidfile)s ] && (cat %(pidfile)s | xargs -r kill %(force)s; true) && rm %(pidfile)s; true" % {"pidfile": util.escape(pidfile), "force": "-9" if force else ""})

def _parentPid(host, pid):
	assert pid
	return int(host.execute("cat /proc/%d/status | fgrep PPid | awk '{print $2}'" % pid))

def killPortUser(host, port):
	assert port
	try:
		res = host.execute("netstat -4tulpn | fgrep :%d" % port)
		for line in res.splitlines():
			try:
				pid = int(line.split()[-1].split("/")[0])
				try:
					host.execute("fgrep 'while true' < /proc/%(pid)d/cmdline >/dev/null && [ $(readlink /proc/%(pid)d/exe) == '/bin/bash' ] && kill %(pid)d" % {"pid": _parentPid(host, pid)})
				except:
					pass
				host.execute("kill %d" % pid)
			except:
				pass
	except exceptions.CommandError:
		pass	

def portFree(host, port):
	try:
		res = host.execute("netstat -4tuln | fgrep :%d" % port)
		return len(res.splitlines()) == 0 
	except exceptions.CommandError:
		return True

def processRunning(host, pidfile, name=""):
	cmdline = util.lines(host.execute("[ -f %(pidfile)s ] && (cat %(pidfile)s | xargs -r ps --no-headers --format cmd --pid); true" % {"pidfile": util.escape(pidfile)}))
	if not len(cmdline):
		return False
	if name:
		return name in cmdline[0]
		