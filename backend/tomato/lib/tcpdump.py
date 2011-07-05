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

import ifaceutil, fileutil, process, hostserver, util

def _tcpdump(host, cmd):
	return host.execute("tcpdump %s" % cmd)
	
def _remoteDir(name):
	return "%s/%s" % (config.REMOTE_DIR, name)
	
def _checkSyntax(host, iface, filter):
	ifaceutil.ifup(host, iface)
	return _tcpdump(host, "-i %s -d '%s' >/dev/null 2>&1; echo $?" % (iface, filter)).strip() == "0"
	
def startCaptureToFile(host, name, iface, filter=""):
	assert name, "Name not given"
	assert ifaceutil.interfaceExists(host, iface), "Interface does not exist"
	assert _checkSyntax(host, iface, filter), "Syntax error: tcpdump -i %s %s" % (iface, filter)
	rdir = _remoteDir(name) 
	fileutil.mkdir(host, rdir)
	ifaceutil.ifup(host, iface)
	_tcpdump(host, "-i %(iface)s -n -C 10 -w %(rdir)s/capture -U -W 5 -s0 '%(filter)s' >/dev/null 2>&1 </dev/null & echo $! > %(rdir)s.file.pid" % {"iface": iface, "rdir": rdir, "filter": filter })		

def captureToFileRunning(host, name="_dummy"):
	return process.processRunning(host, "%s.file.pid" % _remoteDir(name), "tcpdump")

def stopCaptureToFile(host, name):
	rdir = _remoteDir(name)
	process.killPidfile(host, "%s.file.pid" % rdir)

def startCaptureViaNet(host, name, port, iface, filter=""):
	assert name, "Name not given"
	assert port, "Port not given"
	assert ifaceutil.interfaceExists(host, iface), "Interface does not exist"
	assert process.portFree(host, port), "Port already in use"
	assert _checkSyntax(host, iface, filter), "Syntax error: tcpdump -i %s %s" % (iface, filter)
	rdir = _remoteDir(name) 
	fileutil.mkdir(host, rdir)
	ifaceutil.ifup(host, iface)
	host.execute("tcpserver -qHRl 0 0 %(port)s tcpdump -i %(iface)s -nUw - '%(filter)s' >/dev/null 2>&1 </dev/null & echo $! > %(rdir)s.net.pid" % {"iface": iface, "rdir": rdir, "filter": filter, "port": port })
	assert not process.portFree(host, port)

def captureViaNetRunning(host, name="_dummy"):
	return process.processRunning(host, "%s.net.pid" % _remoteDir(name), "tcpserver")

def stopCaptureViaNet(host, name, port):
	rdir = _remoteDir(name)
	process.killPidfile(host, "%s.net.pid" % rdir)
	process.killPortUser(host, port)
	assert process.portFree(host, port)

def removeCapture(host, name):
	rdir = _remoteDir(name)
	fileutil.delete(host, rdir, recursive=True)
	fileutil.delete(host, "%s.*.pid" % rdir)
			
def downloadCaptureUri(host, name):
	filename = "%s.pcap" % name
	path = hostserver.randomFilename(host)
	host.execute("tcpslice -w %s %s/*" % (path, _remoteDir(name)))
	assert fileutil.existsFile(host, path), "No packages captured yet"
	return hostserver.downloadGrant(host, path, filename)