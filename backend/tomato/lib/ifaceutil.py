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

import util, random, exceptions, decorators

def bridgeExists(host, bridge):
	import fileutil
	return fileutil.existsDir(host, "/sys/class/net/%s/brif" % util.identifier(bridge))

def bridgeCreate(host, bridge):
	try:
		host.execute("brctl addbr %s" % util.escape(bridge))
	except exceptions.CommandError:
		if not bridgeExists(host, bridge):
			raise
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
	host.execute("brctl delbr %s" % util.escape(bridge))
	assert not bridgeExists(host, bridge), "Bridge cannot be removed: %s" % bridge
		
def bridgeInterfaces(host, bridge):
	assert bridgeExists(host, bridge), "Bridge does not exist: %s" % bridge 
	return host.execute("ls /sys/class/net/%s/brif" % util.identifier(bridge)).split()
		
def bridgeDisconnect(host, bridge, iface, deleteBridgeIfLast=False):
	assert bridgeExists(host, bridge), "Bridge does not exist: %s" % bridge
	if not iface in bridgeInterfaces(host, bridge):
		return
	host.execute("brctl delif %s %s" % (util.escape(bridge), util.escape(iface)))
	assert not iface in bridgeInterfaces(host, bridge), "Interface %s could not be removed from bridge %s" % (iface, bridge)
	if deleteBridgeIfLast and not bridgeInterfaces(host, bridge):
		bridgeRemove(host, bridge)
				
def bridgeConnect(host, bridge, iface):
	if iface in bridgeInterfaces(host, bridge):
		return
	assert interfaceExists(host, iface), "Interface does not exist: %s" % iface
	if not bridgeExists(host, bridge):
		bridgeCreate(host, bridge)
	oldbridge = interfaceBridge(host, iface)
	if oldbridge:
		bridgeDisconnect(host, oldbridge, iface)
	host.execute("brctl addif %s %s" % (util.escape(bridge), util.escape(iface)))
	assert iface in bridgeInterfaces(host, bridge), "Interface %s could not be connected to bridge %s" % (iface, bridge)
		
def interfaceBridge(host, iface):
	try:
		return util.lines(host.execute("[ -d /sys/class/net/%s/brport/bridge ] && basename $(readlink /sys/class/net/%s/brport/bridge)" % (util.identifier(iface), util.identifier(iface))))[0]
	except exceptions.CommandError:
		return False
			
def interfaceExists(host, iface):
	import fileutil
	return fileutil.existsDir(host, "/sys/class/net/%s" % util.identifier(iface))

def ifup(host, iface):
	assert interfaceExists(host, iface)
	host.execute("ip link set up %s" % util.escape(iface))

def ifdown(host, iface):
	assert interfaceExists(host, iface)
	host.execute("ip link set down %s" % util.escape(iface))
	
def deleteDefaultRoute(host):
	try:
		host.execute("ip route del default")
	except exceptions.CommandError, exc:
		if exc.errorCode != 8: #RTNETLINK answers: No such process
			raise

def addDefaultRoute(host, via):
	try:
		host.execute("ip route add default via %s" % util.escape(via))
	except exceptions.CommandError, exc:
		if exc.errorCode != 8: #RTNETLINK answers: File exists
			raise
	
def addAddress(host, iface, address):
	try:
		host.execute("ip addr add %s dev %s" % (util.escape(address), util.escape(iface)))
	except exceptions.CommandError, exc:
		if exc.errorCode != 2: #RTNETLINK answers: File exists
			raise
	
def randomIp4():
	return "%d.%d.%d.%d"%(10, random.randint(10, 250), random.randint(10, 250), random.randint(10, 250))	

def isIpv4(s):
	import re
	return re.match("(\d+).(\d+).(\d+).(\d.)", s)

@decorators.retryOnError(errorFilter=lambda x: isinstance(x, exceptions.CommandError) and ("Resource temporarily unavailable" in x.errorMessage or "Bad file descriptor" in x.errorMessage))
def iptables(host, args=[], ipv6=False):
	host.execute(" ".join(["ip6tables" if ipv6 else "iptables"]+args))

def connectInterfaces(host, if1, if2, id, allowIps):
	assert interfaceExists(host, if1)
	assert interfaceExists(host, if2)
	iptablesRemoveRules(host, if1)
	iptablesRemoveRules(host, if2)
	for ip in allowIps:
		iptables(host, ["-A", "INPUT", "-i", util.escape(if1), "-d", util.escape(ip), "-j", "ACCEPT"], not isIpv4(ip))
		iptables(host, ["-A", "INPUT", "-i", util.escape(if2), "-d", util.escape(ip), "-j", "ACCEPT"], not isIpv4(ip))
	iptables(host, ["-A", "INPUT", "-i", util.escape(if1), "-j", "REJECT", "--reject-with", "icmp-net-unreachable"])
	iptables(host, ["-A", "INPUT", "-i", util.escape(if2), "-j", "REJECT", "--reject-with", "icmp-net-unreachable"])
	iptables(host, ["-A", "INPUT", "-i", util.escape(if1), "-j", "REJECT", "--reject-with", "icmp6-no-route"], True)
	iptables(host, ["-A", "INPUT", "-i", util.escape(if2), "-j", "REJECT", "--reject-with", "icmp6-no-route"], True)
	#calculate table ids
	table1 = 1000 + id * 2
	table2 = 1000 + id * 2 + 1
	#create rules to select routing table according to incoming device
	try:
		host.execute ( "ip rule del iif %s" % util.escape(if1) )
	except:
		pass
	try:
		host.execute ( "ip rule del iif %s" % util.escape(if2) )
	except:
		pass
	host.execute ( "ip rule add iif %s table %s" % ( util.escape(if1), util.escape(table1) ))
	host.execute ( "ip rule add iif %s table %s" % ( util.escape(if2), util.escape(table2) ))
	#create routing table with only a default device
	try:
		host.execute ( "ip route del table %s default" % util.escape(table1) )
	except:
		pass
	try:
		host.execute ( "ip route del table %s default" % util.escape(table2) )
	except:
		pass
	host.execute ( "ip route add table %s default dev %s" % ( util.escape(table1), util.escape(if2) ))
	host.execute ( "ip route add table %s default dev %s" % ( util.escape(table2), util.escape(if1) ))
	res = host.execute("ip route get %s from %s iif %s" % (util.escape(randomIp4()), util.escape(randomIp4()), util.escape(if2)))
	assert if1 in res, "route should be %s but was %s" % (if1, res)
	res = host.execute("ip route get %s from %s iif %s" % (util.escape(randomIp4()), util.escape(randomIp4()), util.escape(if1)))
	assert if2 in res, "route should be %s but was %s" % (if2, res)


@decorators.retryOnError(errorFilter=lambda x: isinstance(x, exceptions.CommandError) and ("Resource temporarily unavailable" in x.errorMessage or "Bad file descriptor" in x.errorMessage))
def iptablesRemoveRules(host, device):
	host.execute ( "iptables -S INPUT | fgrep 'i %s ' | sed 's/-A /-D /' | while read rule; do iptables $rule; done" % util.identifier(device) )
	host.execute ( "ip6tables -S INPUT | fgrep 'i %s ' | sed 's/-A /-D /' | while read rule; do ip6tables $rule; done" % util.identifier(device) )

def disconnectInterfaces(host, if1, if2, id):
	#calculate table ids
	table1 = 1000 + id * 2
	table2 = 1000 + id * 2 + 1
	try:
		#remove rules
		host.execute ( "ip rule del iif %s" % util.escape(if1) )
		host.execute ( "ip rule del iif %s" % util.escape(if2) )
		#remove routes
		host.execute ( "ip route del table %s default" % util.escape(table1) )
		host.execute ( "ip route del table %s default" % util.escape(table2) )
		#remove iptables filters
		iptablesRemoveRules(host, if1)
		iptablesRemoveRules(host, if2)
	except exceptions.CommandError, exc:
		if exc.errorCode != 2: #Rule does not exist
			raise
	#remove iptables rules
	iptablesRemoveRules(host, if1)
	iptablesRemoveRules(host, if2)
	
def startDhcp(host, iface):
	for cmd in ["/sbin/dhclient", "/sbin/dhcpcd"]:
		try:
			return host.execute("[ -e %s ] && %s %s" % (cmd, cmd, util.escape(iface)))
		except exceptions.CommandError, err:
			if err.errorCode != 8:
				raise			
	return False

def getRxBytes(host, iface):
	if not interfaceExists(host, iface):
		return 0.0
	return int(host.execute("[ -f /sys/class/net/%s/statistics/rx_bytes ] && cat /sys/class/net/%s/statistics/rx_bytes || echo 0" % (util.identifier(iface), util.identifier(iface))))

def getTxBytes(host, iface):
	if not interfaceExists(host, iface):
		return 0.0
	return int(host.execute("[ -f /sys/class/net/%s/statistics/tx_bytes ] && cat /sys/class/net/%s/statistics/tx_bytes || echo 0" % (util.identifier(iface), util.identifier(iface))))

def reachable(host, ip, iface=None):
	try:
		return bool(ping(host, ip, maxWait=1, iface=iface))
	except:
		return False

def ping(host, ip, samples=10, maxWait=5, iface=None):
	assert samples >= 2
	iface = "" if iface is None else "-I %s" % util.escape(iface)
	cmd = "ping" if isIpv4(ip) else "ping6" 
	res = host.execute("%s -A -c %d -n -q -w %d %s %s" % (cmd, samples, maxWait, iface, util.escape(ip)))
	if not res:
		return
	import re
	spattern = re.compile("(\d+) packets transmitted, (\d+) received(, \+(\d+) errors)?, (\d+)% packet loss, time (\d+)(m?s)")
	dpattern = re.compile("rtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) (m?s)(, pipe \d+)?, ipg/ewma (\d+\.\d+)/(\d+\.\d+) (m?s)")
	summary = False
	details = False
	for line in res.splitlines():
		if spattern.match(line):
			(transmitted, received, dummy, errors, loss, total, unit) = spattern.match(line).groups()
			(transmitted, received, errors, loss, total) = (int(transmitted), int(received), int(errors) if errors else None, float(loss)/100.0, float(total))
			summary = True
		if dpattern.match(line):
			(rttmin, rttavg, rttmax, rttstddev, rttunit, dummy, ipg, ewma, ipg_ewma_unit) = dpattern.match(line).groups()
			(rttmin, rttavg, rttmax, rttstddev, ipg, ewma) = (float(rttmin), float(rttavg), float(rttmax), float(rttstddev), float(ipg), float(ewma))
			details = True
	if not summary or not details or errors:
		return
	import math
	loss = 1.0 - math.sqrt(1.0 - loss)
	avg = rttavg / 2.0
	stddev = rttstddev / 2.0
	if rttunit == "s":
		avg = avg * 1000.0
		stddev = stddev * 1000.0
	return (loss, avg, stddev)

def createIfbs(host, num=100):
	if interfaceExists(host, "ifb%d" % (num-1)):
		return
	host.execute("modprobe ifb numifbs=%d" % num)
	assert interfaceExists(host, "ifb%d" % (num-1))