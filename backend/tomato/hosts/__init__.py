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

import sys, atexit, threading, time, random, uuid

from django.db import models
from django.db.models import Q, Sum

from tomato import config, attributes

from tomato.lib import fileutil, db, process, ifaceutil, qm, vzctl, exceptions, hostserver, decorators

from tomato.generic import State
from tomato.lib.decorators import *

class ClusterState:
	MASTER = "M"
	NODE = "N"
	NONE = "-"

COMMAND_RETRIES = 10

MIN_HOST_VERSION = 0.17

class Host(db.ReloadMixin, attributes.Mixin, models.Model):
	SSH_COMMAND = ["ssh", "-oConnectTimeout=30", "-oStrictHostKeyChecking=no", "-oPasswordAuthentication=false", "-i%s" % config.SSH_KEY]
	RSYNC_COMMAND = ["rsync", "-a", "-e", " ".join(SSH_COMMAND)]
	
	group = models.CharField(max_length=10, validators=[db.nameValidator])
	name = models.CharField(max_length=50, unique=True)
	enabled = models.BooleanField(default=True)
	
	attrs = db.JSONField(default={})

	class Meta:
		ordering=["group", "name"]

	def init(self):
		self.attrs = {}
		resources.createPool(self, "port", 7000, 1000)
		resources.createPool(self, "vmid", 1000, 200)
		resources.createPool(self, "bridge", 1000, 1000)
		resources.createPool(self, "ifb", 0, 500)

	def getResourcePool(self, type):
		return resources.getPool(self, type)

	def getHostServer(self):
		return hostserver.HostServer(self.name, self.getAttribute("hostserver_port"), 
		  self.getAttribute("hostserver_basedir"), self.getAttribute("hostserver_secret_key"))

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
		control_master = tasks.Task("control-master", self.startControlMaster, reverseFn=self.disable)
		login = tasks.Task("login", util.curry(self._checkCmd, ["true", "Login error"]), reverseFn=self.disable, after=control_master)
		tomato_host = tasks.Task("tomato-host", self._checkTomatoHostVersion, reverseFn=self.disable, after=login)
		openvz = tasks.Task("openvz", util.curry(self._checkCmd, ["vzlist -a", "OpenVZ error"]), reverseFn=self.disable, after=login)
		kvm = tasks.Task("kvm", util.curry(self._checkCmd, ["qm list", "KVM error"]), reverseFn=self.disable, after=login)
		hostserver = tasks.Task("hostserver", util.curry(self._checkCmd, ["/etc/init.d/tomato-hostserver status", "Hostserver error"]), reverseFn=self.disable, after=login)
		hostserver_config = tasks.Task("hostserver-config", self.fetchHostserverConfig, reverseFn=self.disable, after=hostserver)
		hostserver_cleanup = tasks.Task("hostserver-cleanup", self.hostserverCleanup, reverseFn=self.disable, after=hostserver)
		templates = tasks.Task("templates", self.fetchAllTemplates, reverseFn=self.disable, after=login)
		folder_exists = tasks.Task("folder-exists", self.folderExists, reverseFn=self.disable, after=login)
		create_ifbs = tasks.Task("ifb-interfaces", self._createIfbs, after=login)
		resources = tasks.Task("resources", self._checkResources, after=create_ifbs)
		other = [login, control_master, tomato_host, openvz, kvm, hostserver, hostserver_config, hostserver_cleanup, templates, folder_exists, resources, create_ifbs]
		enable = tasks.Task("enable", self._enable, after=other)
		return other + [enable]

	def _checkResources(self):
		for pool in self.resourcepool_set.all():
			pool.checkOwners()

	def _createIfbs(self):
		pool = self.getResourcePool("ifb")
		ifaceutil.createIfbs(self, pool.first_num + pool.num_count)
		
	def _enable(self):
		self.deleteAttribute("host_check_error")
		if not self.getAttribute("manually_disabled", False):
			self.enabled = True
			self.save()
		
	def check(self):
		proc = tasks.Process("check")
		proc.add(self.checkTasks())
		return proc.start()

	def apt_update(self):
		proc = tasks.Process("update")
		apt_get_update = tasks.Task("apt-get update", util.curry(self.execute, ["apt-get update"]))
		apt_get_dist_upgrade = tasks.Task("apt-get -y dist-upgrade", util.curry(self.execute, ["apt-get -y dist-upgrade"]), after=apt_get_update)		
		proc.add([apt_get_update, apt_get_dist_upgrade])
		return proc.start()

	def disable(self):
		print "Disabling host %s because of error during check" % self
		fault.log_info("Host disabled", "Disabling host %s because of error during check" % self)
		self.enabled = False
		self.save()
		task = tasks.get_current_task()
		self.setAttribute("host_check_error", "%s, %s" % (task.name, task.result) )

	def _checkCmd(self, cmd, errormsg):
		self.execute(cmd)

	def _checkTomatoHostVersion(self):
		res = self.execute("dpkg-query -s tomato-host | fgrep Version | awk '{ print $2 }'")
		try:
			version = float(res.strip())
		except:
			assert False, "tomato-host not found"
		assert version >= MIN_HOST_VERSION, "tomato-host version error, is %s" % version

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

	@decorators.retryOnError(errorFilter=lambda x: isinstance(x, exceptions.CommandError), waitBetween=5.0, maxRetries=COMMAND_RETRIES)
	def _exec(self, cmd):
		res = util.run_shell(cmd)
		if res[0] != 0:
			raise exceptions.CommandError("localhost", cmd, res[0], res[1])
		return res[1]

	def _sshControlPath(self):
		return config.LOCAL_TMP_DIR + "/ssh/" + self.name
	
	def _sshCommand(self, master=False):
		cmd = Host.SSH_COMMAND[:]
		cmd.append("-oControlMaster=%s" % ("yes" if master else "no"))
		cmd.append("-oControlPath=%s" % self._sshControlPath())
		if master:
			cmd.append("-fN")
		return cmd
	
	def startControlMaster(self):
		if fileutil.existsSocket(util.localhost, self._sshControlPath()): 
			try:
				util.localhost.execute("netstat -l | fgrep %s" % self._sshControlPath())
			except:
				#remove defunct socket
				fileutil.delete(util.localhost, self._sshControlPath())
		if not fileutil.existsSocket(util.localhost, self._sshControlPath()):
			fileutil.mkdir(util.localhost, config.LOCAL_TMP_DIR + "/ssh/")
			import subprocess
			subprocess.Popen(self._sshCommand(True) + ["root@%s" % self.name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	
	def execute(self, command):
		stoken = str(uuid.uuid1())
		cmd = self._sshCommand() + ["root@%s" % self.name, ('echo -e "\n%s"; ' % stoken) + command + ' ; echo -e "\n$?" >&2']
		log_str = self.name + ": " + command + "\n"
		if tasks.get_current_task():
			fd = tasks.get_current_task().output
		else:
			fd = sys.stdout
		fd.write(log_str)
		try:
			res = self._exec(cmd)
		except exceptions.CommandError, exc:
			raise exceptions.ConnectError(self.name, exc.errorCode, exc.errorMessage)
		res = util.removeControlChars(res) #might contain funny characters
		res = res.splitlines()
		assert stoken in res
		res = res[res.index(stoken)+1:]
		retCode = int(res[-1].strip())
		res = "\n".join(res[:-1])
		if not res.endswith("\n"):
			res += "\n"
		fd.write(res)
		if retCode != 0:
			raise exceptions.CommandError(self.name, command, retCode, res)
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
			self.setAttribute("manually_disabled", not properties["enabled"])
			if properties["enabled"]:
				self.check()
			else:
				self.enabled = False
				self.save()
		for t in resources.TYPES:
			pool = self.getResourcePool(t)
			if "%s_start" % t in properties:
				pool.first_num = int(properties["%s_start" % t])
				pool.save()
			if "%s_count" % t in properties:
				pool.num_count = int(properties["%s_count" % t])
				pool.save()
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
			"external_networks": [enb.toDict() for enb in self.externalNetworks()],
			"manually_disabled": self.getAttribute("manually_disabled", False),
			"host_check_errror": self.getAttribute("host_check_error", None)}
		res.update(self.getAttributes().items())
		for t in resources.TYPES:
			pool = self.getResourcePool(t)
			res.update({"%s_start" % t: pool.first_num, "%s_count" % t: pool.num_count})
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
	
def create(host_name, group_name, attrs):
	host = Host(name=host_name, enabled=False, group=group_name)
	host.save()
	host.init()
	host.configure(attrs)
	return host.check()

def change(host_name, group_name, attrs):
	host = get(host_name)
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
import templates, resources
from external_networks import ExternalNetwork, ExternalNetworkBridge
from tomato import fault
from tomato.lib import util, tasks