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

from django.db import models

import config, fault, util, sys, atexit, attributes, tasks, threading
from django.db.models import Q, Sum

class ClusterState:
	MASTER = "M"
	NODE = "N"
	NONE = "-"

class Host(models.Model):
	SSH_COMMAND = ["ssh", "-q", "-oConnectTimeout=30", "-oStrictHostKeyChecking=no", "-oUserKnownHostsFile=/dev/null", "-oPasswordAuthentication=false", "-i%s" % config.remote_ssh_key]
	RSYNC_COMMAND = ["rsync", "-a", "-e", " ".join(SSH_COMMAND)]
	
	group = models.CharField(max_length=10, blank=True)
	name = models.CharField(max_length=50, unique=True)
	enabled = models.BooleanField(default=True)
	attributes = models.ForeignKey(attributes.AttributeSet, default=attributes.create)
	lock = threading.Lock()

	def __unicode__(self):
		return self.name

	def fetchAllTemplates(self):
		for tpl in Template.objects.all(): # pylint: disable-msg=E1101
			tpl.uploadToHost(self)

	def check(self):
		if config.remote_dry_run:
			return "---"
		return tasks.Process("check", tasks=[
		  tasks.Task("login", util.curry(self._checkCmd, ["true", "Login error"]), reverseFn=self.disable),
		  tasks.Task("tomato-host", self._checkTomatoHostVersion, reverseFn=self.disable, depends=["login"]),
		  tasks.Task("openvz", util.curry(self._checkCmd, ["vzctl --version", "OpenVZ error"]), reverseFn=self.disable, depends=["login"]),
		  tasks.Task("kvm", util.curry(self._checkCmd, ["qm list", "KVM error"]), reverseFn=self.disable, depends=["login"]),
		  tasks.Task("ipfw", util.curry(self._checkCmd, ["modprobe ipfw_mod && ipfw list", "Ipfw error"]), reverseFn=self.disable, depends=["login"]),
		  tasks.Task("hostserver", util.curry(self._checkCmd, ["/etc/init.d/tomato-hostserver status", "Hostserver error"]), reverseFn=self.disable, depends=["login"]),
		  tasks.Task("hostserver-config", self.fetchHostserverConfig, reverseFn=self.disable, depends=["hostserver"]),
		  tasks.Task("hostserver-cleanup", self.hostserverCleanup, reverseFn=self.disable, depends=["hostserver"]),
		  tasks.Task("templates", self.fetchAllTemplates, reverseFn=self.disable, depends=["login"]),
		  tasks.Task("save", self.fetchAllTemplates, reverseFn=self.disable, depends=["hostserver-config"]),			
		]).start()

	def disable(self):
		print "Disabling host %s because of error during check" % self
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
		assert version >= 0.6, "tomato-host version error, is %s" % version

	def fetchHostserverConfig(self):
		res = self.execute(". /etc/tomato-hostserver.conf; echo $port; echo $basedir; echo $secret_key").splitlines()
		self.attributes["hostserver_port"] = int(res[0])
		self.attributes["hostserver_basedir"] = res[1]
		self.attributes["hostserver_secret_key"] = res[2]
				
	def hostserverCleanup(self):
		if self.attributes.get("hostserver_basedir"):
			self.execute("find %s -type f -mtime +0 -delete" % self.attributes["hostserver_basedir"])
			
	def clusterState(self):
		try:
			res = self.execute("pveca -i 2>/dev/null | tail -n 1")
			return res.split("\n")[-2].split(" ")[-1]
		except:
			return ClusterState.NONE
				
	def nextFreeVmId (self):
		#FIXME: redesign
		try:
			self.lock.acquire()
			ids = range(int(self.attributes["vmid_start"]),int(self.attributes["vmid_start"])+int(self.attributes["vmid_count"]))
			import openvz
			for dev in openvz.OpenVZDevice.objects.filter(host=self): # pylint: disable-msg=E1101
				if dev.attributes.get("vmid"):
					if int(dev.attributes["vmid"]) in ids:
						ids.remove(int(dev.attributes["vmid"]))
			import kvm
			for dev in kvm.KVMDevice.objects.filter(host=self): # pylint: disable-msg=E1101
				if dev.attributes.get("vmid"):
					if int(dev.attributes["vmid"]) in ids:
						ids.remove(int(dev.attributes["vmid"]))
			return ids[0]
		except:
			raise fault.new(fault.NO_RESOURCES, "No more free VM ids on %s" + self)
		finally:
			self.lock.release()

	def nextFreePort(self):
		#FIXME: redesign
		try:
			self.lock.acquire()
			ids = range(int(self.attributes["port_start"]),int(self.attributes["port_start"])+int(self.attributes["port_count"]))
			import openvz
			for dev in openvz.OpenVZDevice.objects.filter(host=self): # pylint: disable-msg=E1101
				if dev.attributes.get("vnc_port"):
					if int(dev.attributes["vnc_port"]) in ids:
						ids.remove(int(dev.attributes["vnc_port"]))
			import kvm
			for dev in kvm.KVMDevice.objects.filter(host=self): # pylint: disable-msg=E1101
				if dev.attributes.get("vnc_port"):
					if int(dev.attributes["vnc_port"]) in ids:
						ids.remove(int(dev.attributes["vnc_port"]))
			import tinc
			for con in tinc.TincConnection.objects.filter(interface__device__host=self): # pylint: disable-msg=E1101
				if con.attributes.get("tinc_port"):
					if int(con.attributes["tinc_port"]) in ids:
						ids.remove(int(con.attributes["tinc_port"]))
			return ids[0]
		except:
			raise fault.new(fault.NO_RESOURCES, "No more free ports on %s" + self)
		finally:
			self.lock.release()

	def nextFreeBridge(self):
		#FIXME: redesign
		try:
			self.lock.acquire()
			ids = range(int(self.attributes["bridge_start"]),int(self.attributes["bridge_start"])+int(self.attributes["bridge_count"]))
			import generic
			for con in generic.Connection.objects.filter(interface__device__host=self): # pylint: disable-msg=E1101
				if con.attributes.get("bridge_id"):
					if int(con.attributes["bridge_id"]) in ids:
						ids.remove(int(con.attributes["bridge_id"]))
			return ids[0]
		except:
			raise fault.new(fault.NO_RESOURCES, "No more free bridge ids on %s" + self)
		finally:
			self.lock.release()
	
	def _exec(self, cmd):
		if config.TESTING:
			return "\n"
		res = util.run_shell(cmd, config.remote_dry_run)
		#if res[0] == 255:
		#	raise fault.Fault(fault.UNKNOWN, "Failed to execute command %s on host %s: %s" % (cmd, self.name, res) )
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
		if not config.remote_dry_run:
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
			if enb.feature_group == en:
				enb.delete()

	def configure(self, properties): #@UnusedVariable, pylint: disable-msg=W0613
		if "enabled" in properties:
			self.enabled = util.parse_bool(properties["enabled"])
		for key in properties:
			self.attributes[key] = properties[key]
		del self.attributes["enabled"]
		del self.attributes["name"]
		del self.attributes["group"]
		self.save()
	
	def toDict(self):
		"""
		Prepares a host for serialization.
		
		@return: a dict containing information about the host
		@rtype: dict
		"""
		res = {"name": self.name, "group": self.group, "enabled": self.enabled, 
			"device_count": self.device_set.count(), # pylint: disable-msg=E1101
			"externalNetworks": [enb.toDict() for enb in self.externalNetworks()]}
		res.update(self.attributes.items())
		return res

	
class Template(models.Model):
	name = models.CharField(max_length=100)
	type = models.CharField(max_length=12)
	default = models.BooleanField(default=False)
	download_url = models.CharField(max_length=255, default="")
		
	def init(self, name, ttype, download_url):
		import re
		if not re.match("^[a-zA-Z0-9_.]+-[a-zA-Z0-9_.]+$", name) or name.endswith(".tar.gz") or name.endswith(".qcow2"):
			raise fault.new(0, "Name must be in the format NAME-VERSION")
		self.name = name
		self.type = ttype
		self.download_url = download_url
		self.save()

	def setDefault(self):
		Template.objects.filter(type=self.type).update(default=False) # pylint: disable-msg=E1101
		self.default=True
		self.save()
		
	def getFilename(self):
		if self.type == "kvm":
			return "/var/lib/vz/template/qemu/%s.qcow2" % self.name
		if self.type == "openvz":
			return "/var/lib/vz/template/cache/%s.tar.gz" % self.name
	
	def uploadToHost(self, host):
		if host.clusterState() == ClusterState.NODE:
			return
		dst = self.getFilename()
		if self.download_url:
			host.execute("curl -o %(filename)s -sSR -z %(filename)s %(url)s" % {"url": self.download_url, "filename": dst})

	def __unicode__(self):
		return "Template(type=%s,name=%s,default=%s)" %(self.type, self.name, self.default)
			
	def toDict(self):
		"""
		Prepares a template for serialization.
			
		@return: a dict containing information about the template
		@rtype: dict
		"""
		return {"name": self.name, "type": self.type, "default": self.default, "url": self.download_url}

			
class PhysicalLink(models.Model):
	src_group = models.CharField(max_length=10)
	dst_group = models.CharField(max_length=10)
	loss = models.FloatField()
	delay_avg = models.FloatField()
	delay_stddev = models.FloatField()
			
	sliding_factor = 0.25
			
	def adapt(self, loss, delay_avg, delay_stddev):
		self.loss = ( 1.0 - self.sliding_factor ) * self.loss + self.sliding_factor * loss
		self.delay_avg = ( 1.0 - self.sliding_factor ) * self.delay_avg + self.sliding_factor * delay_avg
		self.delay_stddev = ( 1.0 - self.sliding_factor ) * self.delay_stddev + self.sliding_factor * delay_stddev
		self.save()
	
	def toDict(self):
		"""
		Prepares a physical link object for serialization.
		
		@return: a dict containing information about the physical link
		@rtype: dict
		"""
		return {"src": self.src_group, "dst": self.dst_group, "loss": self.loss,
			"delay_avg": self.delay_avg, "delay_stddev": self.delay_stddev}
	

class ExternalNetwork(models.Model):
	type = models.CharField(max_length=50)
	group = models.CharField(max_length=50)
	max_devices = models.IntegerField(null=True)
	avoid_duplicates = models.BooleanField(default=False)

	def hasFreeSlots(self):
		return not (self.max_devices and self.usageCount() >= self.max_devices) 

	def usageCount(self):
		import external
		connectors = external.ExternalNetworkConnector.objects.filter(used_network=self)
		num = connectors.annotate(num_connections=models.Count('connection')).aggregate(Sum('num_connections'))["num_connections__sum"]
		return num if num else 0
		
	def toDict(self, bridges=False):
		"""
		Prepares an object for serialization.
		
		@return: a dict containing information about the object
		@rtype: dict
		"""
		data = {"type": self.type, "group": self.group, "max_devices": (self.max_devices if self.max_devices else False), "avoid_duplicates": self.avoid_duplicates}
		if bridges:
			data["bridges"] = [enb.toDict() for enb in self.externalnetworkbridge_set.all()]
		return data

	
class ExternalNetworkBridge(models.Model):
	host = models.ForeignKey(Host)
	network = models.ForeignKey(ExternalNetwork)
	bridge = models.CharField(max_length=10)

	def toDict(self):
		"""
		Prepares an object for serialization.
		
		@return: a dict containing information about the object
		@rtype: dict
		"""
		return {"host": self.host.name, "type": self.network.type, "group": self.network.group, "bridge": self.bridge}

	
def getHostGroups():
	groups = []
	for h in Host.objects.all(): # pylint: disable-msg=E1101
		if not h.group in groups:
			groups.append(h.group)
	return groups
	
def getHost(name):
	return Host.objects.get(name=name) # pylint: disable-msg=E1101

def getHosts(group=None):
	hosts = Host.objects.all()
	if group:
		hosts = hosts.filter(group=group)
	return hosts

def getBestHost(group):
	all_hosts = Host.objects.filter(enabled=True) # pylint: disable-msg=E1101
	if group:
		all_hosts = all_hosts.filter(group=group)
	hosts = all_hosts.annotate(num_devices=models.Count('device')).order_by('num_devices', '?')
	if len(hosts) > 0:
		return hosts[0]
	else:
		raise fault.new(fault.NO_HOSTS_AVAILABLE, "No hosts available")

def getTemplates(ttype=None):
	tpls = Template.objects.all() # pylint: disable-msg=E1101
	if ttype:
		tpls = tpls.filter(type=ttype)
	return tpls

def getTemplateName(ttype, name):
	try:
		return Template.objects.get(type=ttype, name=name).name # pylint: disable-msg=E1101
	except: #pylint: disable-msg=W0702
		return getDefaultTemplate(ttype)

def getTemplate(ttype, name):
	return Template.objects.get(type=ttype, name=name) # pylint: disable-msg=E1101

def addTemplate(name, template_type, url):
	tpl = Template.objects.create(name=name, type=template_type, download_url=url) # pylint: disable-msg=E1101
	proc = tasks.Process("upload-template")
	for host in getHosts():
		proc.addTask(tasks.Task(host.name, fn=tpl.uploadToHost, args=(host,)))
	return proc.start()
	
def removeTemplate(name):
	Template.objects.filter(name=name).delete() # pylint: disable-msg=E1101
	
def getDefaultTemplate(ttype):
	tpls = Template.objects.filter(type=ttype, default=True) # pylint: disable-msg=E1101
	if tpls.count() >= 1:
		return tpls[0].name
	else:
		return None
	
def create(host_name, group_name, enabled, attrs):
	host = Host(name=host_name, enabled=enabled, group=group_name)
	host.save()
	host.configure(attrs)
	return host.check()

def change(host_name, group_name, enabled, attrs):
	host = getHost(host_name)
	host.enabled=enabled
	host.group=group_name
	host.configure(attrs)
	host.save()
	
def remove(host_name):
	host = getHost(host_name)
	assert len(host.device_set.all()) == 0, "Cannot remove hosts that are used"
	host.delete()
		
def getPhysicalLink(srcg_name, dstg_name):
	return PhysicalLink.objects.get(src_group = srcg_name, dst_group = dstg_name) # pylint: disable-msg=E1101		
		
def getAllPhysicalLinks():
	return PhysicalLink.objects.all() # pylint: disable-msg=E1101		
		
def measureLinkProperties(src, dst):
	res = src.execute("ping -A -c 500 -n -q -w 300 %s" % dst.name)
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
				
def measure_physical_links():
	if config.remote_dry_run:
		return
	for srcg in getHostGroups():
		for dstg in getHostGroups():
			if not srcg == dstg:
				try:
					src = getBestHost(srcg)
					dst = getBestHost(dstg)
					(loss, delay_avg, delay_stddev) = measureLinkProperties(src, dst)
					link = getPhysicalLink(srcg, dstg)
					link.adapt(loss, delay_avg, delay_stddev) 
				except PhysicalLink.DoesNotExist: # pylint: disable-msg=E1101
					PhysicalLink.objects.create(src_group=srcg, dst_group=dstg, loss=loss, delay_avg=delay_avg, delay_stddev=delay_stddev) # pylint: disable-msg=E1101
				except fault.Fault:
					pass

def checkAllHosts():
	for host in getHosts():
		host.check()

if not config.TESTING and not config.MAINTENANCE:				
	measurement_task = util.RepeatedTimer(3600, measure_physical_links)
	measurement_task.start()
	host_check_task = util.RepeatedTimer(3600*6, checkAllHosts)
	host_check_task.start()
	atexit.register(measurement_task.stop)
	atexit.register(host_check_task.stop)

def hostCheck(host):
	return host.check()

def externalNetworks():
	return [en.toDict(True) for en in ExternalNetwork.objects.all()]