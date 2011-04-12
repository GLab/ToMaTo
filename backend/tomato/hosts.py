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

import config, fault, util, sys, atexit, attributes, tasks
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

	def __unicode__(self):
		return self.name

	def fetch_all_templates(self):
		for tpl in Template.objects.all(): # pylint: disable-msg=E1101
			tpl.upload_to_host(self)

	def check_save(self):
		tasks.get_current_task().subtasks_total = 10
		self.check()
		self.save()

	def check(self):
		"""
		Checks if the host is reachable, login works and the needed software is installed
		
		@param task: the task object to use
		@type task: tasks.TaskStatus
		@raise AssertionError: is something looks wrong
		@rtype: None   
		"""
		if config.remote_dry_run:
			return True
		task = tasks.get_current_task()
		
		task.output.write("checking login...\n")
		res = self.execute("true; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "Login error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking for openvz...\n")
		res = self.execute("vzctl --version; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "OpenVZ error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking for kvm...\n")
		res = self.execute("qm list; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "OpenVZ error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking for bridge utils...\n")
		res = self.execute("brctl --version; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "brctl error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking for dummynet...\n")
		res = self.execute("modprobe ipfw_mod && ipfw list; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "dumynet error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking for tinc...\n")
		res = self.execute("tincd --version; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "tinc error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking for curl...\n")
		res = self.execute("curl --version; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "curl error"
		task.subtasks_done = task.subtasks_done + 1

		task.output.write("checking for timeout...\n")
		res = self.execute("timeout 1 true; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "timeout error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking for hostserver...\n")
		res = self.execute("/etc/init.d/tomato-hostserver status; echo $?")
		task.output.write(res)
		assert res.split("\n")[-2] == "0", "hostserver error"
		task.subtasks_done = task.subtasks_done + 1
		
		task.output.write("checking cluster membership...\n")
		cluster_state = self.cluster_state()
		if cluster_state == ClusterState.MASTER:
			task.output.write("node is cluster master\n\n")
		elif cluster_state == ClusterState.NODE:
			task.output.write("node is cluster member\n\n")
		elif cluster_state == ClusterState.NONE:
			task.output.write("node is not part of a cluster\n\n")
		
		self.fetch_hostserver_config()
		self.hostserver_cleanup()
		self.fetch_all_templates()
				
	def fetch_hostserver_config(self):
		res = self.execute(". /etc/tomato-hostserver.conf; echo $port; echo $basedir; echo $secret_key").splitlines()
		self.attributes["hostserver_port"] = int(res[0])
		self.attributes["hostserver_basedir"] = res[1]
		self.attributes["hostserver_secret_key"] = res[2]
				
	def hostserver_cleanup(self):
		if self.attributes.get("hostserver_basedir"):
			self.execute("find %s -type f -mtime +0 -delete" % self.attributes["hostserver_basedir"])
			
	def cluster_state(self):
		res = self.execute("pveca -i 2>/dev/null | tail -n 1")
		return res.split("\n")[-2].split(" ")[-1]
				
	def next_free_vm_id (self):
		ids = range(int(self.attributes["vmid_start"]),int(self.attributes["vmid_start"])+int(self.attributes["vmid_count"]))
		import openvz
		for dev in openvz.OpenVZDevice.objects.filter(host=self): # pylint: disable-msg=E1101
			if dev.attributes.get("vmid"):
				ids.remove(int(dev.attributes["vmid"]))
		import kvm
		for dev in kvm.KVMDevice.objects.filter(host=self): # pylint: disable-msg=E1101
			if dev.attributes.get("vmid"):
				ids.remove(int(dev.attributes["vmid"]))
		try:
			return ids[0]
		except:
			raise fault.new(fault.NO_RESOURCES, "No more free VM ids on %s" + self)

	def next_free_port(self):
		ids = range(int(self.attributes["port_start"]),int(self.attributes["port_start"])+int(self.attributes["port_count"]))
		import openvz
		for dev in openvz.OpenVZDevice.objects.filter(host=self): # pylint: disable-msg=E1101
			if dev.attributes.get("vnc_port"):
				ids.remove(int(dev.attributes["vnc_port"]))
		import kvm
		for dev in kvm.KVMDevice.objects.filter(host=self): # pylint: disable-msg=E1101
			if dev.attributes.get("vnc_port"):
				ids.remove(int(dev.attributes["vnc_port"]))
		import tinc
		for con in tinc.TincConnection.objects.filter(interface__device__host=self): # pylint: disable-msg=E1101
			if con.attributes.get("tinc_port"):
				ids.remove(int(con.attributes["tinc_port"]))
		try:
			return ids[0]
		except:
			raise fault.new(fault.NO_RESOURCES, "No more free ports on %s" + self)

	def next_free_bridge(self):
		ids = range(int(self.attributes["bridge_start"]),int(self.attributes["bridge_start"])+int(self.attributes["bridge_count"]))
		import generic
		for con in generic.Connection.objects.filter(interface__device__host=self): # pylint: disable-msg=E1101
			if con.attributes.get("bridge_id"):
				ids.remove(int(con.attributes["bridge_id"]))
		try:
			return ids[0]
		except:
			raise fault.new(fault.NO_RESOURCES, "No more free bridge ids on %s" + self)
	
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
	
	def _calc_grant(self, params):
		list = [k+"="+v for k, v in params.iteritems() if not k == "grant"]
		list.sort()
		import hashlib
		return hashlib.sha1("&".join(list)+"|"+self.attributes["hostserver_secret_key"]).hexdigest()
	
	def upload_grant(self, filename, redirect):
		import urllib, base64, time
		params={"file": filename, "redirect": base64.b64encode(redirect), "valid_until": str(time.time()+3600)}
		params.update(grant=self._calc_grant(params))
		qstr = urllib.urlencode(params)
		return "http://%s:%s/upload?%s" % (self.name, self.attributes["hostserver_port"], qstr)
	
	def download_grant(self, file, name):
		import time
		params={"file": file, "valid_until": str(time.time()+3600), "name": name}
		params.update(grant=self._calc_grant(params))
		import urllib
		qstr = urllib.urlencode(params)
		return "http://%s:%s/download?%s" % (self.name, self.attributes["hostserver_port"], qstr)

	def file_transfer(self, local_file, host, remote_file, direct=False):
		direct = False #FIXME: remove statement
		if direct:
			src = local_file
		else:
			import uuid
			src = "%s/%s" % (self.attributes["hostserver_basedir"], uuid.uuid1())
			self.file_copy(local_file, src)
		url = self.download_grant(src, "file")
		host.execute("curl -o \"%s\" \"%s\"" % (remote_file, url))
		if not direct:
			self.file_delete(src)
		
	def file_put(self, local_file, remote_file):
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
	
	def file_get(self, remote_file, local_file):
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
	
	def file_move(self, src, dst):
		return self.execute("mv \"%s\" \"%s\"" % (src, dst))
	
	def file_copy(self, src, dst):
		return self.execute("cp -a \"%s\" \"%s\"" % (src, dst))

	def file_chown(self, file, owner, recursive=False):
		return self.execute("chown %s \"%s\" \"%s\"" % ("-r" if recursive else "", owner, file))

	def file_chmod(self, file, mode, recursive=False):
		return self.execute("chmod %s \"%s\" \"%s\"" % ("-r" if recursive else "", mode, file))

	def file_mkdir(self, dir):
		return self.execute("mkdir -p \"%s\"" % dir)

	def file_delete(self, path, recursive=False):
		return self.execute("rm %s -f \"%s\"" % ("-r" if recursive else "", path))

	def _first_line(self, line):
		if not line:
			return line
		line = line.splitlines()
		if len(line) == 0:
			return ""
		else:
			return line[0]

	def process_kill(self, pidfile):
		self.execute("[ -f \"%(pidfile)s\" ] && (cat \"%(pidfile)s\" | xargs -r kill; true) && rm \"%(pidfile)s\"" % {"pidfile": pidfile})

	def free_port(self, port):
		self.execute("for i in $(lsof -i:%s -t); do cat /proc/$i/status | fgrep PPid | cut -f2; done | xargs -r kill" % port)
		self.execute("lsof -i:%s -t | xargs -r kill" % port)

	def bridge_exists(self, bridge):
		if config.remote_dry_run:
			return
		return self._first_line(self.execute("[ -d /sys/class/net/%s/brif ]; echo $?" % bridge)) == "0"

	def bridge_create(self, bridge):
		if config.remote_dry_run:
			return
		self.execute("brctl addbr %s" % bridge)
		assert self.bridge_exists(bridge), "Bridge cannot be created: %s" % bridge
		
	def bridge_remove(self, bridge):
		if config.remote_dry_run:
			return
		self.execute("brctl delbr %s" % bridge)
		assert not self.bridge_exists(bridge), "Bridge cannot be removed: %s" % bridge
		
	def bridge_interfaces(self, bridge):
		if config.remote_dry_run:
			return
		assert self.bridge_exists(bridge), "Bridge does not exist: %s" % bridge 
		return self.execute("ls /sys/class/net/%s/brif" % bridge).split()
		
	def bridge_disconnect(self, bridge, iface):
		if config.remote_dry_run:
			return
		assert self.bridge_exists(bridge), "Bridge does not exist: %s" % bridge
		if not iface in self.bridge_interfaces(bridge):
			return
		self.execute("brctl delif %s %s" % (bridge, iface))
		assert not iface in self.bridge_interfaces(bridge), "Interface %s could not be removed from bridge %s" % (iface, bridge)
		
	def bridge_connect(self, bridge, iface):
		if config.remote_dry_run:
			return
		if iface in self.bridge_interfaces(bridge):
			return
		assert self.interface_exists(iface), "Interface does not exist: %s" % iface
		if not self.bridge_exists(bridge):
			self.bridge_create(bridge)
		oldbridge = self.interface_bridge(iface)
		if oldbridge:
			self.bridge_disconnect(oldbridge, iface)
		self.execute("brctl addif %s %s" % (bridge, iface))
		assert iface in self.bridge_interfaces(bridge), "Interface %s could not be connected to bridge %s" % (iface, bridge)
		
	def interface_bridge(self, iface):
		if config.remote_dry_run:
			return
		return self._first_line(self.execute("[ -d /sys/class/net/%s/brport/bridge ] && basename $(readlink /sys/class/net/%s/brport/bridge)" % (iface, iface)))
			
	def interface_exists(self, iface):
		if config.remote_dry_run:
			return
		return self._first_line(self.execute("[ -d /sys/class/net/%s ]; echo $?" % iface)) == "0"

	def debug_info(self):		
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
	
	def external_networks(self):
		return self.externalnetworkbridge_set.all() # pylint: disable-msg=E1101
	
	def external_networks_add(self, type, group, bridge):
		en = ExternalNetwork.objects.get(type=type, group=group)
		enb = ExternalNetworkBridge(host=self, network=en, bridge=bridge)
		enb.save()
		self.externalnetworkbridge_set.add(enb) # pylint: disable-msg=E1101
		
	def external_networks_remove(self, type, group):
		en = ExternalNetwork.objects.get(type=type, group=group)
		for enb in self.external_networks():
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
	
	def to_dict(self):
		"""
		Prepares a host for serialization.
		
		@return: a dict containing information about the host
		@rtype: dict
		"""
		res = {"name": self.name, "group": self.group, "enabled": self.enabled, 
			"device_count": self.device_set.count(), # pylint: disable-msg=E1101
			"external_networks": [enb.to_dict() for enb in self.external_networks()]}
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

	def set_default(self):
		Template.objects.filter(type=self.type).update(default=False) # pylint: disable-msg=E1101
		self.default=True
		self.save()
		
	def get_filename(self):
		if self.type == "kvm":
			return "/var/lib/vz/template/qemu/%s.qcow2" % self.name
		if self.type == "openvz":
			return "/var/lib/vz/template/cache/%s.tar.gz" % self.name
	
	def upload_to_all(self):
		for host in Host.objects.all(): # pylint: disable-msg=E1101
			self.upload_to_host(host)
		
	def upload_to_host(self, host):
		if host.cluster_state() == ClusterState.NODE:
			return
		dst = self.get_filename()
		if self.download_url:
			host.execute("curl -o %(filename)s -sSR -z %(filename)s %(url)s" % {"url": self.download_url, "filename": dst})

	def __unicode__(self):
		return "Template(type=%s,name=%s,default=%s)" %(self.type, self.name, self.default)
			
	def to_dict(self):
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
	
	def to_dict(self):
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

	def has_free_slots(self):
		return not (self.max_devices and self.usage_count() >= self.max_devices) 

	def usage_count(self):
		import external
		connectors = external.ExternalNetworkConnector.objects.filter(used_network=self)
		num = connectors.annotate(num_connections=models.Count('connection')).aggregate(Sum('num_connections'))["num_connections__sum"]
		return num if num else 0
		
	def to_dict(self, bridges=False):
		"""
		Prepares an object for serialization.
		
		@return: a dict containing information about the object
		@rtype: dict
		"""
		data = {"type": self.type, "group": self.group, "max_devices": (self.max_devices if self.max_devices else False), "avoid_duplicates": self.avoid_duplicates}
		if bridges:
			data["bridges"] = [enb.to_dict() for enb in self.externalnetworkbridge_set.all()]
		return data

	
class ExternalNetworkBridge(models.Model):
	host = models.ForeignKey(Host)
	network = models.ForeignKey(ExternalNetwork)
	bridge = models.CharField(max_length=10)

	def to_dict(self):
		"""
		Prepares an object for serialization.
		
		@return: a dict containing information about the object
		@rtype: dict
		"""
		return {"host": self.host.name, "type": self.network.type, "group": self.network.group, "bridge": self.bridge}

	
def get_host_groups():
	groups = []
	for h in Host.objects.all(): # pylint: disable-msg=E1101
		if not h.group in groups:
			groups.append(h.group)
	return groups
	
def get_host(name):
	return Host.objects.get(name=name) # pylint: disable-msg=E1101

def get_hosts(group=None):
	hosts = Host.objects.all()
	if group:
		hosts = hosts.filter(group=group)
	return hosts

def get_best_host(group):
	all_hosts = Host.objects.filter(enabled=True) # pylint: disable-msg=E1101
	if group:
		all_hosts = all_hosts.filter(group=group)
	hosts = all_hosts.annotate(num_devices=models.Count('device')).order_by('num_devices', '?')
	if len(hosts) > 0:
		return hosts[0]
	else:
		raise fault.new(fault.NO_HOSTS_AVAILABLE, "No hosts available")

def get_templates(ttype=None):
	tpls = Template.objects.all() # pylint: disable-msg=E1101
	if ttype:
		tpls = tpls.filter(type=ttype)
	return tpls

def get_template_name(ttype, name):
	try:
		return Template.objects.get(type=ttype, name=name).name # pylint: disable-msg=E1101
	except: #pylint: disable-msg=W0702
		return get_default_template(ttype)

def get_template(ttype, name):
	return Template.objects.get(type=ttype, name=name) # pylint: disable-msg=E1101

def add_template(name, template_type, url):
	tpl = Template.objects.create(name=name, type=template_type, download_url=url) # pylint: disable-msg=E1101
	import tasks
	t = tasks.TaskStatus(tpl.upload_to_all)
	t.subtasks_total = 1
	t.start()
	return t.id
	
def remove_template(name):
	Template.objects.filter(name=name).delete() # pylint: disable-msg=E1101
	
def get_default_template(ttype):
	tpls = Template.objects.filter(type=ttype, default=True) # pylint: disable-msg=E1101
	if tpls.count() >= 1:
		return tpls[0].name
	else:
		return None
	
def create(host_name, group_name, enabled, attrs):
	host = Host(name=host_name, enabled=enabled, group=group_name)
	host.save()
	host.configure(attrs)
	import tasks
	t = tasks.TaskStatus(host.check_save)
	t.subtasks_total = 1
	t.start()
	return t.id

def change(host_name, group_name, enabled, attrs):
	host = get_host(host_name)
	host.enabled=enabled
	host.group=group_name
	host.configure(attrs)
	host.save()
	
def remove(host_name):
	host = get_host(host_name)
	assert len(host.device_set.all()) == 0, "Cannot remove hosts that are used"
	host.delete()
		
def get_physical_link(srcg_name, dstg_name):
	return PhysicalLink.objects.get(src_group = srcg_name, dst_group = dstg_name) # pylint: disable-msg=E1101		
		
def get_all_physical_links():
	return PhysicalLink.objects.all() # pylint: disable-msg=E1101		
		
def measure_link_properties(src, dst):
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
	for srcg in get_host_groups():
		for dstg in get_host_groups():
			if not srcg == dstg:
				try:
					src = get_best_host(srcg)
					dst = get_best_host(dstg)
					(loss, delay_avg, delay_stddev) = measure_link_properties(src, dst)
					link = get_physical_link(srcg, dstg)
					link.adapt(loss, delay_avg, delay_stddev) 
				except PhysicalLink.DoesNotExist: # pylint: disable-msg=E1101
					PhysicalLink.objects.create(src_group=srcg, dst_group=dstg, loss=loss, delay_avg=delay_avg, delay_stddev=delay_stddev) # pylint: disable-msg=E1101
				except fault.Fault:
					pass

def check_all_hosts():
	if config.remote_dry_run:
		return
	tasks.set_current_task(tasks.TaskStatus(None))
	for host in get_hosts():
		try:
			if host.enabled:
				host.check()
		except Exception, exc:
			print "Disabling host %s because or error during check: %s" % (h, exc)
			host.enabled = False
			host.save()
	tasks.get_current_task().done()
	tasks.set_current_task(None)

if not config.TESTING:				
	measurement_task = util.RepeatedTimer(3600, measure_physical_links)
	measurement_task.start()
	host_check_task = util.RepeatedTimer(3600*6, check_all_hosts)
	host_check_task.start()
	atexit.register(measurement_task.stop)
	atexit.register(host_check_task.stop)

def host_check(host):
	t = tasks.TaskStatus(host.check)
	t.subtasks_total = 7
	t.start()
	return t.id

def external_networks():
	return [en.to_dict(True) for en in ExternalNetwork.objects.all()]