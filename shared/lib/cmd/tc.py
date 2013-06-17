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

from . import run, CommandError
import math

def _tc(type, action, params=[]): #@ReservedAssignment
	return run(["tc", type, action]+params)
	
def _buildNetem(bandwidth=None, delay=0.0, jitter=0.0, delay_correlation=0.0, distribution=None, lossratio=0.0, loss_correlation=0.0, duplicate=0.0, corrupt=0.0):
	netem = ["netem"]
	if bandwidth:
		"""
		Need to set a packet limit for netem. Otherwise netem will buffer all
		packets until they can be consumed by the rate limit, thereby 
		preventing them from being dropped and increasing the delay infinitely.
		"""
		limit = 10
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
			limit = max(math.ceil(max(delay, jitter/2.0) * bandwidth / 2000.0), 10.0)
		netem += ["limit", str(limit)]
	if delay or jitter or delay_correlation:
		assert delay >= 0.0
		assert jitter >= 0.0
		assert 100.0 >= delay_correlation >= 0.0
		netem += ["delay", "%fms" % delay, "%fms" % jitter, "%f%%" % delay_correlation]
	if delay and jitter and distribution:
		assert distribution in ["uniform", "normal", "pareto", "paretonormal"]
		if distribution != "uniform":
			netem += ["distribution", str(distribution)]
	if lossratio or loss_correlation:
		assert 100.0 >= lossratio >= 0.0
		assert 100.0 >= loss_correlation >= 0.0
		netem += ["loss", "%f%%" % lossratio,  "%f%%" % loss_correlation]
	if duplicate:
		assert 100.0 >= duplicate >= 0.0
		netem += ["duplicate", "%f%%" % duplicate]
	if corrupt:
		assert 100.0 >= corrupt >= 0.0
		netem += ["corrupt",  "%f%%" % corrupt]
	return netem

def _buildTbf(bandwidth):
	assert bandwidth > 0.0
	tbf = ["tbf"]
	tbf += ["rate", "%fKbit" % bandwidth]
	maxDuration = 25.0
	mtu = 1540.0
	tbf += ["latency", "%fms" % maxDuration]
	bufferBytes = max(math.ceil(bandwidth / 8.0 * maxDuration), mtu)
	tbf += ["buffer", str(int(bufferBytes))]
	#if mtu / 8.0 < bandwidth < 1000.0:
		#no idea what mtu / 8.0 should mean but that is the boundary of tc
	#	tbf.append("peakrate %fKbit" % bandwidth)
	#	tbf.append("mtu %d" % int(mtu))
	return tbf

def setLinkEmulation(dev, bandwidth=None, keepBandwidth=False, **kwargs):
	netem_ref = ["dev", dev, "root", "handle", "1:0"]
	if not bandwidth is None:
		netem_ref = ["dev", dev, "parent", "1:1", "handle", "10:"]
		if not keepBandwidth:
			_tc("qdisc", "replace", ["dev", dev, "root", "handle", "1:"] + _buildTbf(bandwidth))
	_tc("qdisc", "replace", netem_ref + _buildNetem(bandwidth=bandwidth, **kwargs))
	
def clearLinkEmulation(dev):
	try:
		_tc("qdisc", "del", ["root", "dev", dev])
	except CommandError, exc:
		if not "No such file or directory" in exc.errorMessage:
			raise

def setIncomingRedirect(srcDev, dstDev):
	try:
		_tc("qdisc", "del", ["dev", srcDev, "ingress"])
	except:
		pass
	_tc("qdisc", "add", ["dev", srcDev, "ingress"])
	""" 
	Protocol all would forward all traffic but that results
	in ARP traffic being multiplied and causing lots of traffic
	""" 
	_tc("filter", "replace", ["dev", srcDev, "parent", "ffff:", 
							 "protocol", "all", "prio", "49152", "u32", "match", "u32", "0", "0", "flowid", "1:1",
							 "action", "mirred", "egress", "redirect", "dev", dstDev])
		
def clearIncomingRedirect(host, dev):
	_tc("qdisc", "del", "dev", dev, "ingress")
	_tc("filter", "del", "dev", dev, "parent", "ffff:", "prio", "49152")