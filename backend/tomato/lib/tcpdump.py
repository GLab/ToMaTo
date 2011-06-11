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

from tomato import config

import ifaceutil, fileutil, process, hostserver

def _tcpdump(host, cmd):
	return host.execute("tcpdump %s" % cmd)
	
def _remoteDir(name):
	return "%s/%s" % (config.REMOTE_DIR, name)
	
def _checkSyntax(host, iface, filter):
	return _tcpdump(host, "-i %s -d %s >/dev/null 2>&1; echo $?" % (iface, filter)).strip() == "0"
	
def startCapture(host, name, iface, filter=""):
	assert name, "Name not given"
	assert ifaceutil.interfaceExists(host, iface), "Interface does not exist"
	assert _checkSyntax(host, iface, filter), "Syntax error: tcpdump -i %s %s" % (iface, filter)
	rdir = _remoteDir(name) 
	fileutil.mkdir(host, rdir)
	_tcpdump(host, "-i %(iface)s -n -C 10 -w %(rdir)s/capture -W 5 -s0 %(filter)s >/dev/null 2>&1 </dev/null & echo $! > %(rdir)s.pid" % {"iface": iface, "rdir": rdir, "filter": filter })		

def captureRunning(host, name):
	return process.processRunning(host, "%s.pid" % _remoteDir("_dummy"), "tcpdump")

def stopCapture(host, name):
	rdir = _remoteDir(name)
	process.killPidfile(host, "%s.pid" % rdir)

def removeCapture(host, name):
	rdir = _remoteDir(name)
	fileutil.delete(host, rdir, recursive=True)
	fileutil.delete(host, "%s.pid" % rdir)
			
def downloadCaptureUri(host, name):
	filename = "%s.tar.gz" % name
	path = hostserver.randomFilename(host)
	fileutil.packdir(host, path, _remoteDir(name))
	return hostserver.downloadGrant(host, path, filename)