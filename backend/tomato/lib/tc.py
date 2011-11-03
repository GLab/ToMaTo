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

import ifaceutil, exceptions, math, util

def _tc_cmd(type, action, ref, params=""):
	return "tc %s %s %s %s" % (type, action, ref, params)
	
def _buildNetem(bandwidth=None, delay=0.0, jitter=0.0, delay_correlation=0.0, distribution=None, loss=0.0, loss_correlation=0.0, duplicate=0.0, corrupt=0.0):
	netem = ["netem"]
	if bandwidth:
		"""
		Need to set a packet limit for netem. Otherwise netem will buffer all
		packets until they can be consumed by the rate limit, thereby 
		preventing them from being dropped and increasing the delay infinitely.
		"""
		limit = 1
		if delay or jitter:
			"""
			The average packet consumption rate of the rate limiter is:
			 pcrate = bandwidth * 1024 / 8 / pktsize
			Example: bandwidth=4kbit/s, pktsize=512b, pcrate=1/s
			The netem qdisc must be able to process at least that rate of
			packages without causing loss.
			The average delay of a packet can be calculated as:
			 avgdelay = max(delay, jitter/2) / 1000
			Thus, on average pcrate * avgdelay packets must be buffered.
			We are taking the double to be sure.
			Assumption: pktsize=512b 
			""" 
			limit = math.ceil(max(delay, jitter/2.0) * bandwidth / 2000.0)
		netem.append("limit %d" % limit)
	if delay or jitter or delay_correlation:
		assert delay >= 0.0
		assert jitter >= 0.0
		assert 100.0 >= delay_correlation >= 0.0
		netem.append("delay %fms %fms %f%%" % (delay, jitter, delay_correlation))
	if delay and jitter and distribution:
		assert distribution in ["uniform", "normal", "pareto", "paretonormal"]
		netem.append("distribution %s" % distribution)
	if loss or loss_correlation:
		assert 100.0 >= loss >= 0.0
		assert 100.0 >= loss_correlation >= 0.0
		netem.append("loss %f%% %f%%" % (loss, loss_correlation))
	if duplicate:
		assert 100.0 >= duplicate >= 0.0
		netem.append("duplicate %f%%" % duplicate)
	if corrupt:
		assert 100.0 >= corrupt >= 0.0
		netem.append("corrupt %f%%" % corrupt)
	return " ".join(netem)

def _buildTbf(bandwidth):
	assert bandwidth > 0.0
	tbf = ["tbf"]
	tbf.append("rate %fKbit" % bandwidth)
	maxDuration = 25.0
	mtu = 1540.0
	tbf.append("latency %fms" % maxDuration)
	bufferBytes = max(math.ceil(bandwidth / 8.0 * maxDuration), mtu)
	tbf.append("buffer %d" % int(bufferBytes))
	#if mtu / 8.0 < bandwidth < 1000.0:
		#no idea what mtu / 8.0 should mean but that is the boundy of tc
	#	tbf.append("peakrate %fKbit" % bandwidth)
	#	tbf.append("mtu %d" % int(mtu))
	return " ".join(tbf)

def setLinkEmulation(host, dev, bandwidth=None, keepBandwidth=False, **kwargs):
	assert ifaceutil.interfaceExists(host, dev)
	netem_ref = "dev %s root handle 1:0" % util.escape(dev)
	cmd = ""
	if not bandwidth is None:
		netem_ref = "dev %s parent 1:1 handle 10:" % util.escape(dev)
		if not keepBandwidth:
			cmd = _tc_cmd("qdisc", "replace", "dev %s root handle 1:" % util.escape(dev), _buildTbf(bandwidth))
			cmd += ";"
	cmd += _tc_cmd("qdisc", "replace", netem_ref, _buildNetem(bandwidth=bandwidth, **kwargs))
	host.execute(cmd)
	
def clearLinkEmulation(host, dev):
	assert ifaceutil.interfaceExists(host, dev)
	try:
		host.execute(_tc_cmd("qdisc", "del", "root dev %s" % util.escape(dev)))
	except exceptions.CommandError, exc:
		if not "No such file or directory" in exc.errorMessage:
			raise

def setIncomingRedirect(host, srcDev, dstDev):
	assert ifaceutil.interfaceExists(host, srcDev)
	assert ifaceutil.interfaceExists(host, dstDev)
	try:
		host.execute(_tc_cmd("qdisc", "del", "dev %s ingress" % util.escape(srcDev)))
	except:
		pass
	host.execute(_tc_cmd("qdisc", "add", "dev %s ingress" % util.escape(srcDev)))
	""" 
	Protocol all would forward all traffic but that results
	in ARP traffic being multiplied and causing lots of traffic
	""" 
	host.execute(_tc_cmd("filter", "replace", "dev %s parent ffff:" % util.escape(srcDev), \
	 "protocol all prio 49152 u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev %s" % util.escape(dstDev)))
		
def clearIncomingRedirect(host, dev):
	assert ifaceutil.interfaceExists(host, dev)
	host.execute(_tc_cmd("qdisc", "del", "dev %s ingress" % util.escape(dev)))
	host.execute(_tc_cmd("filter", "del", "dev %s parent ffff: prio 49152" % util.escape(dev)))