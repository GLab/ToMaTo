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

from .. import util
from . import run, CommandError
from process import killTree
import path
import os, re, random

def getIfbCount():
	def _ifbExists(n):
		return os.path.exists("/sys/class/net/ifb%d" % n)
	#check if 0 exists
	if not _ifbExists(0):
		return 0
	max_ = 1
	while _ifbExists(max_):
		max_ *= 2
	min_ = max_/2
	while max_ - min_ > 1: #binary search
		n = (min_ + max_)/2
		if _ifbExists(n):
			min_ = n
		else:
			max_ = n
	return min_ + 1 #min is the number, +1 is the count

def _ifacePath(ifname):
	return "/sys/class/net/%s" % ifname

def ifaceExists(ifname):
	return path.exists(_ifacePath(ifname))

def linkConfig(ifname, options=[]):
	run(["ip", "link", "set", ifname]+options)
	
def ifUp(ifname):
	linkConfig(ifname, ["up"])

def ifDown(ifname):
	linkConfig(ifname, ["down"])
	
def interfaceBridge(ifname):
	brlink = os.path.join(_ifacePath(ifname), "brport/bridge")
	if not path.exists(brlink):
		return None
	return path.basename(path.readlink(brlink))
	
def trafficInfo(ifname):
	if not ifaceExists(ifname):
		return (None, None)
	with open(os.path.join(_ifacePath(ifname), "statistics/tx_bytes")) as fp:
		tx = int(fp.readline().strip())
	with open(os.path.join(_ifacePath(ifname), "statistics/rx_bytes")) as fp:
		rx = int(fp.readline().strip())
	return (rx, tx)

def tcpPortUsed(port):
	return bool(tcpPortUsers(port))

def tcpPortUsers(port):
	try:
		res = run(["lsof", "-ti", "TCP:%d" % port])
		return [int(line.strip()) for line in res.splitlines()]
	except:
		return []
	
def freeTcpPort(port):
	pids = tcpPortUsers(port)
	for pid in pids:
		killTree(pid)
	if not util.waitFor(lambda :not tcpPortUsed(port)):
		pids = tcpPortUsers(port)
		for pid in pids:
			killTree(pid, force=True)
	

def _brifPath(brname):
	return os.path.join(_ifacePath(brname), "brif")

def bridgeExists(brname):
	return path.exists(_brifPath(brname))

def bridgeCreate(brname):
	run(["brctl", "addbr", brname])
	
def bridgeInterfaces(brname):
	assert bridgeExists(brname)
	return path.entries(_brifPath(brname))

def bridgeRemove(brname):
	assert not bridgeInterfaces(brname)
	assert bridgeExists(brname)
	ifDown(brname)
	run(["brctl", "delbr", brname])
	
	
def bridgeAddInterface(brname, ifname):
	assert bridgeExists(brname)
	assert ifaceExists(ifname)
	run(["brctl", "addif", brname, ifname])
	
def bridgeRemoveInterface(brname, ifname):
	assert bridgeExists(brname)
	assert ifaceExists(ifname)
	if ifname in bridgeInterfaces(brname):
		run(["brctl", "delif", brname, ifname])
		
def ping(dst, count=100, timeout=1.0, totalTimeout=100.0):
	try:
		res = run(["ping", dst, "-Aqn", "-c", str(count), "-w", str(totalTimeout), "-W", str(timeout)])
		match = re.search("(\d+) packets transmitted, (\d+) received, (\d+)% packet loss, time (\d+)ms\nrtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) ms", res)
		if match:
			tx, rx, loss, _, rttMin, rttAvg, rttMax, rttMdev = match.groups()
			tx, rx = map(int, [tx, rx])
			loss = int(loss)/100.0
			rttMin, rttAvg, rttMax, rttMdev = map(lambda s: float(s)/1000.0, [rttMin, rttAvg, rttMax, rttMdev])
			return {"transmitted": tx, "received": rx, "loss": loss, "rtt_min": rttMin, "rtt_avg": rttAvg, "rtt_max": rttMax, "rtt_mdev": rttMdev}
	except:
		pass
	return {"transmitted": count, "received": 0, "loss": 1.0}

def tcpslice(outfile, entries, limitSize=None):
	run(["tcpslice", "-Dw", outfile] + entries)
	if not limitSize or path.filesize(outfile) < limitSize:
		return
	times = run(["tcpslice", "-RDw", "/dev/null"] + entries)
	times = [line.split() for line in times.splitlines()]
	minTime = min([float(t[1]) for t in times])
	maxTime = max([float(t[2]) for t in times])
	while maxTime - minTime > 1.0:
		t = (minTime + maxTime)/2.0
		run(["tcpslice", "-Dw", outfile, str(t)] + entries)
		size = path.filesize(outfile)
		if size > limitSize:
			minTime = t
		else:
			maxTime = t
	run(["tcpslice", "-Dw", outfile, str(maxTime)] + entries)
	
def randomMac():
	bytes = [random.randint(0x00, 0xff) for _ in xrange(6)]
	bytes[0] = bytes[0] & 0xfc | 0x02 # local and individual
	return ':'.join(map(lambda x: "%02x" % x, bytes))