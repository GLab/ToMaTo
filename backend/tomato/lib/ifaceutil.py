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

import tomato.config as config

from tomato import util

def bridgeExists(host, bridge):
	if config.remote_dry_run:
		return
	return util.lines(host.execute("[ -d /sys/class/net/%s/brif ]; echo $?" % bridge))[0] == "0"

def bridgeCreate(host, bridge):
	if config.remote_dry_run:
		return
	host.execute("brctl addbr %s" % bridge)
	assert bridgeExists(host, bridge), "Bridge cannot be created: %s" % bridge
		
def bridgeRemove(host, bridge):
	if config.remote_dry_run:
		return
	host.execute("brctl delbr %s" % bridge)
	assert not bridgeExists(host, bridge), "Bridge cannot be removed: %s" % bridge
		
def bridgeInterfaces(host, bridge):
	if config.remote_dry_run:
		return
	assert bridgeExists(host, bridge), "Bridge does not exist: %s" % bridge 
	return host.execute("ls /sys/class/net/%s/brif" % bridge).split()
		
def bridgeDisconnect(host, bridge, iface):
	if config.remote_dry_run:
		return
	assert bridgeExists(host, bridge), "Bridge does not exist: %s" % bridge
	if not iface in bridgeInterfaces(host, bridge):
		return
	host.execute("brctl delif %s %s" % (bridge, iface))
	assert not iface in bridgeInterfaces(host, bridge), "Interface %s could not be removed from bridge %s" % (iface, bridge)
		
def bridgeConnect(host, bridge, iface):
	if config.remote_dry_run:
		return
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
	if config.remote_dry_run:
		return
	return util.lines(host.execute("[ -d /sys/class/net/%s/brport/bridge ] && basename $(readlink /sys/class/net/%s/brport/bridge)" % (iface, iface)))[0]
			
def interfaceExists(host, iface):
	if config.remote_dry_run:
		return
	return util.lines(host.execute("[ -d /sys/class/net/%s ]; echo $?" % iface))[0] == "0"

def ifup(host, iface):
	assert interfaceExists(host, iface)
	host.execute("ip link set up %s" % iface)

def ifdown(host, iface):
	assert interfaceExists(host, iface)
	host.execute("ip link set down %s" % iface)
	
def getRxBytes(host, iface):
	assert interfaceExists(host, iface)
	return int(host.execute("[ -f /sys/class/net/%s/statistics/rx_bytes ] && cat /sys/class/net/%s/statistics/rx_bytes || echo 0"))

def getTxBytes(host, iface):
	assert interfaceExists(host, iface)
	return int(host.execute("[ -f /sys/class/net/%s/statistics/tx_bytes ] && cat /sys/class/net/%s/statistics/tx_bytes || echo 0"))