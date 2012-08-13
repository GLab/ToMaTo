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

import random, math, shutil

from tomato import generic, config

import process, fileutil, ifaceutil, util, tasks, exceptions

CONFIG_TEMPLATE = """
options {
  port %(port)d;
}

client {
  password %(password)s;
  type ether;
  proto udp;
  device %(iface)s;
  multi yes;
  persist keep;
  up {
    ip "link set %%%% up";
    program "brctl addif %(bridge)s %%%%";
  }
}
"""

def _vtunName(port):
	return "vtun_%d" % port
	
def _pidFile(port):
	return "/var/run/vtund.%d.pid" % port

def _configPath(port):
	return config.REMOTE_DIR + "/vtun/%d.conf" % port
	
def getState(host, port):
	assert host
	if not fileutil.existsFile(host, _configPath(port)):
		return generic.State.CREATED
	if not fileutil.existsFile(host, _pidFile(port)):
		return generic.State.PREPARED
	if not process.processRunning(host, _pidFile(port), "vtund"):
		return generic.State.PREPARED
	return generic.State.STARTED
	
def start(host, port):
	assert host
	assert process.portFree(host, port)
	host.execute("vtund -s -f %s" % _configPath(port))
	util.waitFor(lambda :fileutil.existsFile(host, "/var/run/vtund.server.pid"), 5.0)
	assert fileutil.existsFile(host, "/var/run/vtund.server.pid")
	fileutil.copy(host, "/var/run/vtund.server.pid", _pidFile(port))

def stop(host, port):
	assert getState(host, port) != generic.State.CREATED
	assert host
	process.killPidfile(host, _pidFile(port))
	util.waitFor(lambda :getState(host, port) == generic.State.PREPARED, 5.0)
	assert getState(host, port) == generic.State.PREPARED

def _tmpFile(port):
	return "%s/%s" % ( config.LOCAL_TMP_DIR, _vtunName(port) )
	
def _createConfigFile(port, password, bridge):
	path = _tmpFile(port)
	confFd = open(path, "w")
	confFd.write(CONFIG_TEMPLATE % {"port": port, "password": password, "bridge": bridge, "iface": _vtunName(port)})
	confFd.close()

def _removeTemporaryFiles(port):
	fileutil.delete(util.localhost, _tmpFile(port))

def _uploadConfig(host, port):
	if getState(host, port) == generic.State.PREPARED:
		_deleteConfig(host, port)
	assert getState(host, port) == generic.State.CREATED, "vtun config file exists: %d" % port
	host.filePut(_tmpFile(port), _configPath(port))

def _deleteConfig(host, port):
	assert getState(host, port) != generic.State.STARTED
	fileutil.delete(host, _configPath(port))
	
def prepare(host, port, password, bridge):
	_createConfigFile(port, password, bridge)
	_uploadConfig(host, port)
	_removeTemporaryFiles(port)
	
def destroy(host, port):
	_deleteConfig(host, port)