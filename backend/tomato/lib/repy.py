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

from tomato import generic, config

import process, fileutil, util, ifaceutil

def _path(vmid, ext):
	return  "%s/repy/%s.%s" % (config.REMOTE_DIR, vmid, ext)	

def _imagePath(vmid):
	return _path(vmid, "repy")

def _logFile(vmid):
	return _path(vmid, "log")

def _pidFile(vmid):
	return _path(vmid, "pid")

def _vncPidFile(vmid):
	return _path(vmid, "vnc-pid")

def getState(host, vmid):
	if process.processRunning(host, _pidFile(vmid), "python"):
		return generic.State.STARTED
	if fileutil.existsFile(host, _imagePath(vmid)):
		return generic.State.PREPARED
	return generic.State.CREATED

def startVnc(host, vmid, port, password):
	assert getState(host, vmid) == generic.State.STARTED, "VM must be running to start vnc"
	assert process.portFree(host, port)
	host.execute("( while true; do vncterm -rfbport %d -passwd %s -c tail -f %s ; done ) >/dev/null 2>&1 & echo $! > %s" % ( port, password, _logFile(vmid), _vncPidFile(vmid) ))
	assert not process.portFree(host, port)

def stopVnc(host, vmid, port):
	process.killPidfile(host, _vncPidFile(vmid))
	process.killPortUser(host, port)
	assert process.portFree(host, port)
	
def _templatePath(name):
	return "/var/lib/vz/template/repy/%s.repy" % name

def create(host, vmid, template):
	assert getState(host, vmid) == generic.State.CREATED, "VM already exists"
	fileutil.mkdir(host, "%s/repy" % config.REMOTE_DIR)
	fileutil.copy(host, _templatePath(template), _imagePath(vmid))
	assert getState(host, vmid) == generic.State.PREPARED, "Failed to create VM"
	
def start(host, vmid, ifaces, args=[]):
	assert getState(host, vmid) == generic.State.PREPARED, "VM already running"
	ilist = ["-i repy%s.%s,alias=%s" % (vmid, i, i) for i in ifaces]
	if isinstance(args, basestring):
		args = [args]
	alist = [util.escape(a) for a in args] 
	host.execute("tomato-repy -p %s -v %s %s > %s 2>&1 & echo $! > %s" % (_imagePath(vmid), " ".join(ilist), " ".join(alist), _logFile(vmid), _pidFile(vmid) ))
	assert getState(host, vmid) == generic.State.STARTED, "Repy device failed to start"
	for i in ifaces:
		waitForInterface(host, vmid, i)

def waitForInterface(host, vmid, iface):
	util.waitFor(lambda :ifaceutil.interfaceExists(host, interfaceDevice(vmid, iface)))

def stop(host, vmid):
	assert getState(host, vmid) != generic.State.CREATED, "VM not running"
	process.killPidfile(host, _pidFile(vmid))
	fileutil.delete(host, _logFile(vmid))
	assert getState(host, vmid) == generic.State.PREPARED, "Failed to stop VM"

def destroy(host, vmid):
	assert getState(host, vmid) != generic.State.STARTED, "VM not stopped"
	fileutil.delete(host, _imagePath(vmid))
	fileutil.delete(host, _logFile(vmid))
	fileutil.delete(host, _pidFile(vmid))
	fileutil.delete(host, _vncPidFile(vmid))
	assert getState(host, vmid) == generic.State.CREATED, "Failed to destroy VM"

def useImage(host, vmid, image):
	assert getState(host, vmid) == generic.State.PREPARED, "VM not prepared"
	assert fileutil.existsFile(host, image), "Image does not exist"
	fileutil.copy(host, image, _imagePath(vmid))	

def copyImage(host, vmid, file):
	assert getState(host, vmid) != generic.State.CREATED, "VM must be prepared"
	fileutil.copy(host, _imagePath(vmid), file)	
	assert fileutil.existsFile(host, file)

def getDiskUsage(host, vmid):
	state = getState(host, vmid)
	if state == generic.State.CREATED:
		return 0
	else:
		return int(host.execute("[ -s %(path)s ] && stat -c %%s %(path)s || echo 0" % {"path": _imagePath(vmid)}))
	
def getMemoryUsage(host, vmid):
	if getState(host, vmid) == generic.State.STARTED:
		return int(host.execute("( [ -s %(pidfile)s ] && PROC=`head -n1 %(pidfile)s` && [ -e /proc/$PROC/stat ] && cat /proc/$PROC/stat ) 2>/dev/null | awk '{print ($24 * 4096)}' || echo 0" % {"pidfile": _pidFile(vmid)}))
	else:
		return 0

def interfaceDevice(vmid, iface):
	return "repy%s.%s" % ( vmid, iface )