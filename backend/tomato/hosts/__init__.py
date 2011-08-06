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

import sys, atexit, threading

from django.db import models
from django.db.models import Q, Sum

from tomato import config, attributes

from tomato.lib import fileutil, db, process, ifaceutil, qm, vzctl

from tomato.generic import State
from tomato.lib.decorators import *

class ClusterState:
	MASTER = "M"
	NODE = "N"
	NONE = "-"

class Host(db.ReloadMixin, attributes.Mixin, models.Model):
	SSH_COMMAND = ["ssh", "-q", "-oConnectTimeout=30", "-oStrictHostKeyChecking=no", "-oUserKnownHostsFile=/dev/null", "-oPasswordAuthentication=false", "-i%s" % config.SSH_KEY]
	RSYNC_COMMAND = ["rsync", "-a", "-e", " ".join(SSH_COMMAND)]
	
	group = models.CharField(max_length=10, validators=[db.nameValidator])
	name = models.CharField(max_length=50, unique=True)
	enabled = models.BooleanField(default=True)
	
	attrs = db.JSONField(default={})
	
	lock = threading.Lock()

	def init(self):
		self.attrs = {}
		self.setAttribute("port_start", 7000)
		self.setAttribute("port_count", 1000)
		self.setAttribute("vmid_start", 1000)
		self.setAttribute("vmid_count", 200)
		self.setAttribute("bridge_start", 1000)
		self.setAttribute("bridge_count", 1000)

	def __unicode__(self):
		return self.name

	def fetchAllTemplates(self):
		for tpl in templates.getAll(): # pylint: disable-msg=E1101
			tpl.uploadToHost(self)

	def folderExists(self):
		if not fileutil.existsDir(self, config.REMOTE_DIR):
			fileutil.mkdir(self, config.REMOTE_DIR)
		assert fileutil.existsDir(self, config.REMOTE_DIR)

	def checkTasks(self):
		login = tasks.Task("login", util.curry(self._checkCmd, ["true", "Login error"]), reverseFn=self.disable)
		tomato_host = tasks.Task("tomato-host", self._checkTomatoHostVersion, reverseFn=self.disable, after=login)
		openvz = tasks.Task("openvz", util.curry(self._checkCmd, ["vzctl --version", "OpenVZ error"]), reverseFn=self.disable, after=login)
		kvm = tasks.Task("kvm", util.curry(self._checkCmd, ["qm list", "KVM error"]), reverseFn=self.disable, after=login)
		ipfw = tasks.Task("ipfw", util.curry(self._checkCmd, ["modprobe ipfw_mod && ipfw list", "Ipfw error"]), reverseFn=self.disable, after=login)
		hostserver = tasks.Task("hostserver", util.curry(self._checkCmd, ["/etc/init.d/tomato-hostserver status", "Hostserver error"]), reverseFn=self.disable, after=login)
		hostserver_config = tasks.Task("hostserver-config", self.fetchHostserverConfig, reverseFn=self.disable, after=hostserver)
		hostserver_cleanup = tasks.Task("hostserver-cleanup", self.hostserverCleanup, reverseFn=self.disable, after=hostserver)
		templates = tasks.Task("templates", self.fetchAllTemplates, reverseFn=self.disable, after=login)
		folder_exists = tasks.Task("folder-exists", self.folderExists, reverseFn=self.disable, after=login)
		free_ids = tasks.Task("id-usage", self._checkIds, after=login)
		return [login, tomato_host, openvz, kvm, ipfw, hostserver, hostserver_config, hostserver_cleanup, templates, folder_exists, free_ids]
		
	def check(self):
		proc = tasks.Process("check")
		proc.add(self.checkTasks())
		return proc.start()

	def disable(self):
		print "Disabling host %s because of error during check" % self
		fault.errors_add("Host disabled", "Disabling host %s because of error during check" % self)
		self.enabled = False
		self.save()

	def _checkCmd(self, cmd, errormsg):
		res = self.execute("%s; echo $?" % cmd)
		assert res.split("\n")[-2] == "0", errormsg

	def _checkTomatoHostVersion(self):
		res = self.execute("dpkg-query -s tomato-host | fgrep Version | awk '{ print $2 }'")
		try:
			version = float(res.strip())
		except:
			assert False, "tomato-host not found"
		assert version >= 0.9, "tomato-host version error, is %s" % version

	def fetchHostserverConfig(self):
		res = self.execute(". /etc/tomato-hostserver.conf; echo $port; echo $basedir; echo $secret_key").splitlines()
		self.setAttribute("hostserver_port", int(res[0]))
		self.setAttribute("hostserver_basedir", res[1])
		self.setAttribute("hostserver_secret_key", res[2])
				
	def hostserverCleanup(self):
		if self.hasAttribute("hostserver_basedir"):
			self.execute("find %s -type f -mtime +0 -delete" % self.getAttribute("hostserver_basedir"))
			
	def clusterState(self):
		try:
			res = self.execute("pveca -i 2>/dev/null | tail -n 1")
			return res.split("\n")[-2].split(" ")[-1]
		except:
			return ClusterState.NONE
				
	def hostServerBasedir(self):
		return self.getAttribute("hostserver_basedir") 

	def _calcFreeIds(self):
		types = ["vmid", "port", "bridge"]
		ids = {}
		for t in types:
			ids[t] = range(self.getAttribute("%s_start" % t),self.getAttribute("%s_start" % t)+self.getAttribute("%s_count" % t))
		from tomato import topology
		for top in topology.all():
			usage = top.getIdUsage(self)
			for (t, used) in usage.iteritems():
				assert t in types, "Unknown id type: %s" % t
				assert set(ids[t]) >= used, "Topology %s uses %s ids that are not available: %s" % (top, t, used-set(ids[t]))
				ids[t] = list(set(ids[t]) - used)
		return ids			
				
	def _getFreeIds(self):
		self.reload()
		if self.getAttribute("free_ids"):
			return self._unpackIds(self.getAttribute("free_ids"))
		ids = self._calcFreeIds()
		self._setFreeIds(ids)
		return ids

	def _setFreeIds(self, ids):
		self.setAttribute("free_ids", self._packIds(ids))
		self.save()
			
	def _packList(self, ids):
		packed = []
		start = None
		last = None
		for i in sorted(ids):
			assert isinstance(i, int), "List items must be int, was %s: %s" % (type(i), i)
			if not last or (i != last + 1):
				if not start is None:
					if start == last:
						packed.append(last)
					else:
						packed.append((start, last))						
				start = i
				last = i
			else:
				last += 1
		if not start is None:
			if start == last:
				packed.append(last)
			else:
				packed.append((start, last))
		return packed
				
	def _unpackList(self, packed):
		ids = []
		for i in packed:
			if not isinstance(i, int):
				i = tuple(i)
				(start, end) = i
				ids.extend(range(start, end+1))
			else:
				ids.append(i)
		return ids

	def _packIds(self, ids):
		packed = {}
		for (key, value) in ids.iteritems():
			packed[key] = self._packList(value)
		return packed

	def _unpackIds(self, packed):
		ids = {}
		for (key, value) in packed.iteritems():
			ids[key] = self._unpackList(value)
		return ids

	def _checkIds(self):
		unused = self._calcFreeIds()
		unclaimed = self._getFreeIds()
		types = ["vmid", "port", "bridge"]
		for t in types:
			for id in set(unused[t]) - set(unclaimed[t]):
				# id is claimed but unused
				realUsage = self._realIdState(t, id)
				if realUsage:
					self._freeId(t, id)
				fault.errors_add("Free id mismatch", "%s %d on host %s is claimed but not used by any topology. Its real usage was %s." % (t, id, self.name, realUsage))
			for id in set(unclaimed[t]) - set(unused[t]):
				# id is used but not claimed
				fault.errors_add("Free id mismatch", "%s %d on host %s is used by a topology but not claimed." % (t, id, self.name))
			self._setFreeIds(unused)
				
	def _realIdState(self, type, id):
		if type == "vmid":
			return qm.getState(self, id) != State.CREATED or vzctl.getState(self, id) != State.CREATED
		elif type == "port":
			return not process.portFree(self, id)
		elif type == "bridge":
			return ifaceutil.bridgeExists(self, "gbr_%d" % id) 

	def _freeId(self, type, id):
		if type == "vmid":
			if qm.getState(self, id) == State.STARTED:
				qm.stop(self, id)
			if qm.getState(self, id) == State.PREPARED:
				qm.destroy(self, id)
			if vzctl.getState(self, id) == State.STARTED:
				vzctl.stop(self, id)
			if vzctl.getState(self, id) == State.PREPARED:
				vzctl.destroy(self, id)
		elif type == "port":
			process.killPortUser(self, id)
		elif type == "bridge":
			ifaceutil.bridgeRemove(self, "gbr_%d" % id, True, True)

	def takeId(self, type, callback):
		try:
			Host.lock.acquire()
			#print "enter"
			ids = self._getFreeIds()
			fault.check(len(ids[type]), "No more free %ss on host %s", (type, self.name))
			#print "Free %s ids: %s" % (type, self._packList(ids[type]))
			#print "Callback: %s" % callback
			id = sorted(ids[type])[0]
			#print "Taken %s: %s" % (type, id)
			ids[type].remove(id)
			self._setFreeIds(ids)
			callback(id)
			#print "taken free %s: %d" % (type, id)
			#assert not id in self._calcFreeIds()[type], "Id was not properly reserved"
			#print "exit"
		finally:
			Host.lock.release()
			
	def giveId(self, type, id):
		try:
			Host.lock.acquire()
			assert id in xrange(self.getAttribute("%s_start" % type),self.getAttribute("%s_start" % type)+self.getAttribute("%s_count" % type))
			ids = self._getFreeIds()
			assert not id in ids[type], "%s %s was not reserved" % (type, id)
			ids[type].append(id)
			self._setFreeIds(ids) 
			#print "returned free %s: %d" % (type, id)
		finally:
			Host.lock.release()			
	
	def _exec(self, cmd):
		res = util.run_shell(cmd)
		return res[1]
	
	def execute(self, command):
		cmd = Host.SSH_COMMAND + ["root@%s" % self.name, command]
		log_str = self.name + ": " + command + "\n"
		if tasks.get_current_task():
			fd = tasks.get_current_task().output
		else:
			fd = sys.stdout
		fd.write(log_str)
		res = self._exec(cmd)
		res = util.removeControlChars(res) #might contain funny characters
		fd.write(res)
		return res
	
	def filePut(self, local_file, remote_file):
		cmd = Host.RSYNC_COMMAND + [local_file, "root@%s:%s" % (self.name, remote_file)]
		log_str = self.name + ": " + local_file + " -> " + remote_file  + "\n"
		self.execute("mkdir -p $(dirname %s)" % remote_file)
		if tasks.get_current_task():
			fd = tasks.get_current_task().output
		else:
			fd = sys.stdout
		fd.write(log_str)
		res = self._exec(cmd)
		fd.write(res)
		return res

	def fileGet(self, remote_file, local_file):
		cmd = Host.RSYNC_COMMAND + ["root@%s:%s" % (self.name, remote_file), local_file]
		log_str = self.name + ": " + local_file + " <- " + remote_file  + "\n"
		if tasks.get_current_task():
			fd = tasks.get_current_task().output
		else:
			fd = sys.stdout
		fd.write(log_str)
		res = self._exec(cmd)
		fd.write(res)
		return res

	def _firstLine(self, line):
		if not line:
			return line
		line = line.splitlines()
		if len(line) == 0:
			return ""
		else:
			return line[0]

	def debugInfo(self):		
		result={}
		result["top"] = self.execute("top -b -n 1")
		result["OpenVZ"] = self.execute("vzlist -a")
		result["KVM"] = self.execute("qm list")
		result["Bridges"] = self.execute("brctl show")
		result["iptables router"] = self.execute("iptables -t mangle -v -L PREROUTING")		
		result["ipfw rules"] = self.execute("ipfw show")
		result["ipfw pipes"] = self.execute("ipfw pipe show")
		result["ifconfig"] = self.execute("ifconfig -a")
		result["netstat"] = self.execute("netstat -tulpen")		
		result["df"] = self.execute("df -h")		
		result["templates"] = self.execute("ls -lh /var/lib/vz/template/*")		
		result["hostserver"] = self.execute("/etc/init.d/tomato-hostserver status")		
		result["hostserver-files"] = self.execute("ls -l /var/lib/vz/hostserver")		
		return result
	
	def externalNetworks(self):
		return self.externalnetworkbridge_set.all() # pylint: disable-msg=E1101
	
	def externalNetworksAdd(self, type, group, bridge):
		en = ExternalNetwork.objects.get(type=type, group=group)
		enb = ExternalNetworkBridge(host=self, network=en, bridge=bridge)
		enb.save()
		self.externalnetworkbridge_set.add(enb) # pylint: disable-msg=E1101
		
	def externalNetworksRemove(self, type, group):
		en = ExternalNetwork.objects.get(type=type, group=group)
		for enb in self.externalNetworks():
			if enb.network == en:
				enb.delete()

	def configure(self, properties): #@UnusedVariable, pylint: disable-msg=W0613
		if "enabled" in properties:
			self.enabled = util.parse_bool(properties["enabled"])
		for var in ["vmid_start", "vmid_count", "port_start", "port_count", "bridge_start", "bridge_count"]:
			if var in properties:
				self.setAttribute(var, int(properties[var]))
		if "group" in properties:
			self.group = properties["group"]
		self.save()
	
	def toDict(self):
		"""
		Prepares a host for serialization.
		
		@return: a dict containing information about the host
		@rtype: dict
		"""
		res = {"name": self.name, "group": self.group, "enabled": self.enabled, 
			"device_count": self.device_set.count(), # pylint: disable-msg=E1101
			"external_networks": [enb.toDict() for enb in self.externalNetworks()]}
		res.update(self.getAttributes().items())
		return res
	
def getGroups():
	groups = []
	for h in Host.objects.all(): # pylint: disable-msg=E1101
		if not h.group in groups:
			groups.append(h.group)
	return groups
	
def get(name):
	return Host.objects.get(name=name) # pylint: disable-msg=E1101

def getAll(group=None):
	hosts = Host.objects.all()
	if group:
		hosts = hosts.filter(group=group)
	return hosts

def getBest(group):
	all_hosts = Host.objects.filter(enabled=True) # pylint: disable-msg=E1101
	if group:
		all_hosts = all_hosts.filter(group=group)
	hosts = all_hosts.annotate(num_devices=models.Count('device')).order_by('num_devices', '?')
	fault.check(hosts, "No hosts available")
	return hosts[0]
	
def create(host_name, group_name, enabled, attrs):
	host = Host(name=host_name, enabled=enabled, group=group_name)
	host.save()
	host.init()
	host.configure(attrs)
	return host.check()

def change(host_name, group_name, enabled, attrs):
	host = get(host_name)
	host.enabled=enabled
	host.group=group_name
	host.configure(attrs)
	host.save()
	
def remove(host_name):
	host = get(host_name)
	fault.check(len(host.device_set.all()) == 0, "Cannot remove hosts that are used")
	host.delete()
						
def checkAll():
	for host in getAll():
		proc = tasks.Process("check-%s" % host.name, host.checkTasks())
		proc.run()

def check(host):
	return host.check()

# keep internal imports at the bottom to avoid dependency problems
import templates
from external_networks import ExternalNetwork, ExternalNetworkBridge
from tomato import fault
from tomato.lib import util, tasks