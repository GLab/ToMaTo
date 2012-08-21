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

from tomato.host import run
import path
import os

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
	run(["brctl", "delif", brname, ifname])