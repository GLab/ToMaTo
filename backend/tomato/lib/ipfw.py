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

import tcpdump, ifaceutil

def _ipfw(host, cmd):
	return host.execute("ipfw %s" % cmd)

def _startDummyCapture(host):
	# Due to some weird kernel optimization bridges get sometimes skipped
	# and the link emulation will not work.
	# Using the pcap interface seams to prevent this issue
	if not ifaceutil.bridgeExists(host, "dummy"):
		ifaceutil.bridgeCreate(host, "dummy")
	ifaceutil.ifup(host, "dummy")
	if not tcpdump.captureRunning(host, "_dummy"):
		tcpdump.startCapture(host, "_dummy", "dummy")

def configurePipe(host, pipe, delay=0, bandwidth=None, lossratio=0.0):
	assert pipeExists(host, pipe), "Pipe does not exist %s on host %s" % (pipe, host)
	_startDummyCapture(host)
	pipe_config=""
	if delay:
		delay = int(delay)
		pipe_config = pipe_config + " " + "delay %dms" % delay
	if bandwidth:			
		bandwidth = int(bandwidth)
		pipe_config = pipe_config + " " + "bw %dk" % bandwidth
	if lossratio:
		lossratio = float(lossratio)
		pipe_config = pipe_config + " " + "plr %f" % lossratio
	_ipfw(host, "pipe %d config %s" % ( pipe, pipe_config ))
		
def loadModule(host):
	host.execute("modprobe ipfw_mod")
	assert moduleLoaded(host), "ipfw not loaded"

def moduleLoaded(host):
	res = host.execute("lsmod | fgrep -q ipfw_mod; echo $?")
	return res[0] == "0"

def pipeExists(host, pipe):
	res = host.execute("ipfw show %d >/dev/null 2>&1; echo $?" % pipe)
	return res[0] == "0"

def createPipe(host, pipe, iface, dir="out"):
	assert moduleLoaded(host), "ipfw not loaded"
	assert iface
	if pipeExists(host, pipe):
		deletePipe(host, pipe)
	_ipfw(host, "add %d pipe %d via %s %s" % ( pipe, pipe, iface, dir ))
	assert pipeExists(host, pipe), "failed to create pipe"

def deletePipe(host, pipe):
	_ipfw(host, "delete %d" % pipe)
	_ipfw(host, "pipe delete %d" % pipe)
