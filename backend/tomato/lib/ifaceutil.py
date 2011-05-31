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

import util

def bridgeExists(host, bridge):
	return util.lines(host.execute("[ -d /sys/class/net/%s/brif ]; echo $?" % bridge))[0] == "0"

def bridgeCreate(host, bridge):
	host.execute("brctl addbr %s" % bridge)
	assert bridgeExists(host, bridge), "Bridge cannot be created: %s" % bridge
		
def bridgeRemove(host, bridge, disconnectAll=False, setIfdown=True):
	if not bridgeExists(host, bridge):
		return
	if disconnectAll:
		for iface in bridgeInterfaces(host, bridge):
			bridgeDisconnect(host, bridge, iface)
	assert not bridgeInterfaces(host, bridge)
	if setIfdown:
		ifdown(host, bridge)
	host.execute("brctl delbr %s" % bridge)
	assert not bridgeExists(host, bridge), "Bridge cannot be removed: %s" % bridge
		
def bridgeInterfaces(host, bridge):
	assert bridgeExists(host, bridge), "Bridge does not exist: %s" % bridge 
	return host.execute("ls /sys/class/net/%s/brif" % bridge).split()
		
def bridgeDisconnect(host, bridge, iface):
	assert bridgeExists(host, bridge), "Bridge does not exist: %s" % bridge
	if not iface in bridgeInterfaces(host, bridge):
		return
	host.execute("brctl delif %s %s" % (bridge, iface))
	assert not iface in bridgeInterfaces(host, bridge), "Interface %s could not be removed from bridge %s" % (iface, bridge)
		
def bridgeConnect(host, bridge, iface):
	if iface in bridgeInterfaces(host, bridge):
		return
	assert interfaceExists(host, iface), "Interface does not exist: %s" % iface
	if not bridgeExists(host, bridge):
		bridgeCreate(host, bridge)
	oldbridge = interfaceBridge(host, iface)
	if oldbridge:
		bridgeDisconnect(host, oldbridge, iface)
	host.execute("brctl addif %s %s" % (bridge, iface))
	assert iface in bridgeInterfaces(host, bridge), "Interface %s could not be connected to bridge %s" % (iface, bridge)
		
def interfaceBridge(host, iface):
	return util.lines(host.execute("[ -d /sys/class/net/%s/brport/bridge ] && basename $(readlink /sys/class/net/%s/brport/bridge)" % (iface, iface)))[0]
			
def interfaceExists(host, iface):
	return util.lines(host.execute("[ -d /sys/class/net/%s ]; echo $?" % iface))[0] == "0"

def ifup(host, iface):
	assert interfaceExists(host, iface)
	host.execute("ip link set up %s" % iface)

def ifdown(host, iface):
	assert interfaceExists(host, iface)
	host.execute("ip link set down %s" % iface)
	
def setDefaultRoute(host, via):
	host.execute("ip route add default via %s" % via)
	
def addAddress(host, iface, address):
	host.execute("ip addr add %s dev %s" % (address, iface))
	
def startDhcp(host, iface):
	host.execute("\"[ -e /sbin/dhclient ] && /sbin/dhclient %s\"" % iface)
	host.execute("\"[ -e /sbin/dhcpcd ] && /sbin/dhcpcd %s\"" % iface)
	
def getRxBytes(host, iface):
	assert interfaceExists(host, iface)
	return int(host.execute("[ -f /sys/class/net/%s/statistics/rx_bytes ] && cat /sys/class/net/%s/statistics/rx_bytes || echo 0"))

def getTxBytes(host, iface):
	assert interfaceExists(host, iface)
	return int(host.execute("[ -f /sys/class/net/%s/statistics/tx_bytes ] && cat /sys/class/net/%s/statistics/tx_bytes || echo 0"))

def ping(host, ip, samples=10, maxWait=5):
	res = host.execute("ping -A -c %d -n -q -w %d %s" % (samples, maxWait, ip))
	if not res:
		return
	lines = res.splitlines()
	loss = float(lines[3].split()[5][:-1])/100.0
	import math
	loss = 1.0 - math.sqrt(1.0 - loss)
	times = lines[4].split()[3].split("/")
	unit = lines[4].split()[4][:-1]
	avg = float(times[1]) / 2.0
	stddev = float(times[3]) / 2.0
	if unit == "s":
		avg = avg * 1000.0
		stddev = stddev * 1000.0
	return (loss, avg, stddev)
