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

import ifaceutil, exceptions, math

def _tc(host, type, action, ref, params=""):
	return host.execute("tc %s %s %s %s" % (type, action, ref, params))

def _tc_mod(host, type, ref, params=""):
	try:
		return _tc(host, type, "change", ref, params)
	except exceptions.CommandError:
		try:
			return _tc(host, type, "replace", ref, params)
		except exceptions.CommandError:
			_tc(host, type, "del", ref)
			return _tc(host, type, "add", ref, params)
	
def _buildNetem(delay=0.0, jitter=0.0, delay_correlation=0.0, distribution=None, loss=0.0, loss_correlation=0.0, duplicate=0.0, corrupt=0.0):
	netem = ["netem"]
	if delay or jitter or delay_correlation:
		assert delay >= 0.0
		assert jitter >= 0.0
		assert 100.0 >= delay_correlation >= 0.0
		netem.append("delay %fms %fms %f%%" % (delay, jitter, delay_correlation))
	if distribution:
		assert distribution in ["normal", "pareto", "normalpareto"]
		netem.append("distribution %s" % distribution)
	if loss or loss_correlation:
		assert 100.0 >= loss >= 0.0
		assert 100.0 >= loss_correlation >= 0.0
		netem.append("loss %f%% %f%%" % (loss, loss_correlation))
	if duplicate:
		assert 100.0 >= duplicate >= 0.0
		netem.appen("duplicate %f%%" % duplicate)
	if corrupt:
		assert 100.0 >= corrupt >= 0.0
		netem.appen("duplicate %f%%" % corrupt)
	return " ".join(netem)

def _buildTbf(bandwidth):
	assert bandwidth > 0.0
	tbf = ["tbf"]
	tbf.append("rate %fKbit" % bandwidth)
	maxDuration = 25.0
	mtu = 1600.0
	tbf.append("latency %fms" % maxDuration)
	bufferBytes = max(math.ceil(bandwidth / 8.0 * maxDuration), mtu)
	tbf.append("buffer %d" % int(bufferBytes))
	if bandwidth < 1000.0:
		tbf.append("peakrate %fKbit" % bandwidth)
	return " ".join(tbf)

def setLinkEmulation(host, dev, bandwidth=None, **kwargs):
	assert ifaceutil.interfaceExists(host, dev)
	netem_ref = "dev %s root handle 1:0" % repr(dev)
	if not bandwidth is None:
		netem_ref = "dev %s parent 1:1 handle 10:" % repr(dev)
		_tc_mod(host, "qdisc", "dev %s root handle 1:" % repr(dev), _buildTbf(bandwidth))
	_tc_mod(host, "qdisc", netem_ref, _buildNetem(**kwargs))
	
def clearLinkEmulation(host, dev):
	assert ifaceutil.interfaceExists(host, dev)
	_tc(host, "qdisc", "del", "root dev %s" % repr(dev))

def setIncomingRedirect(host, srcDev, dstDev):
	assert ifaceutil.interfaceExists(host, srcDev)
	assert ifaceutil.interfaceExists(host, dstDev)
	_tc_mod(host, "qdisc", "dev %s ingress" % repr(srcDev))
	_tc_mod(host, "filter", "dev %s parent ffff:" % repr(srcDev), \
	 "protocol all prio 49152 u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev %s" % repr(dstDev))
		
def clearIncomingRedirect(host, dev):
	assert ifaceutil.interfaceExists(host, dev)
	_tc(host, "qdisc", "del", "dev %s ingress" % repr(dev))
	_tc(host, "filter", "del", "dev %s parent ffff: prio 49152" % repr(dev))