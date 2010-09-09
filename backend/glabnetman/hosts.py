# -*- coding: utf-8 -*-

from django.db import models

import config, fault, util, sys

class HostGroup(models.Model):
	name = models.CharField(max_length=10)
	
class Host(models.Model):
	group = models.ForeignKey(HostGroup)
	name = models.CharField(max_length=50, unique=True)
	public_bridge = models.CharField(max_length=10)

	def check_save(self, task):
		task.subtasks_total = 5
		self.check(task)
		self.save()
		task.done()

	def check(self, task):
		"""
		Checks if the host is reachable, login works and the needed software is installed
		"""
		from util import run_shell
		task.output.write("checking for openvz...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "vzctl --version" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write("checking for bridge utils...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "brctl show" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write("checking for dummynet...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "ipfw -h" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
		task.output.write("checking for tinc...\n")
		task.output.write(run_shell (["ssh",  "root@%s" % self.name, "tincd --version" ], config.remote_dry_run))
		task.subtasks_done = task.subtasks_done + 1
				
	def next_free_vm_id (self):
		ids = range(1000,1100)
		import openvz
		for dev in openvz.OpenVZDevice.objects.filter(host=self, openvz_id__isnull=False):
			ids.remove(dev.openvz_id)
		import kvm
		for dev in kvm.KVMDevice.objects.filter(host=self, kvm_id__isnull=False):
			ids.remove(dev.kvm_id)
		return ids[0]

	def next_free_port(self):
		ids = range(7000,8000)
		import openvz
		for dev in openvz.OpenVZDevice.objects.filter(host=self, vnc_port__isnull=False):
			ids.remove(dev.vnc_port)
		import kvm
		for dev in kvm.KVMDevice.objects.filter(host=self, vnc_port__isnull=False):
			ids.remove(dev.vnc_port)
		import tinc
		for con in tinc.TincConnection.objects.filter(interface__device__host=self, tinc_port__isnull=False):
			ids.remove(con.tinc_port)
		return ids[0]

	def next_free_bridge(self):
		ids = range(1000,2000)
		import generic
		for con in generic.Connection.objects.filter(interface__device__host=self, bridge_id__isnull=False):
			ids.remove(con.bridge_id)
		return ids[0]
	
	def _exec(self, cmd):
		return util.run_shell(cmd, config.remote_dry_run)
	
	def execute(self, command, task=None):
		cmd = ["ssh", "root@%s" % self.name, command]
		str = self.name + ": " + command + "\n"
		if task:
			fd = task.output
		else:
			fd = sys.stdout
		fd.write(str)
		res = self._exec(cmd)
		fd.write(res)
		return res
	
	def upload(self, local_file, remote_file, task=None):
		cmd = ["rsync", "-a", local_file, "root@%s:%s" % (self.name, remote_file)]
		str = self.name + ": " + local_file + " -> " + remote_file  + "\n"
		self.execute("mkdir -p $(dirname %s)" % remote_file, task)
		if task:
			fd = task.output
		else:
			fd = sys.stdout
		fd.write(str)
		res = self._exec(cmd)
		fd.write(res)
		return res
	
	def download(self, remote_file, local_file, task=None):
		cmd = ["rsync", "-a", "root@%s:%s" % (self.name, remote_file), local_file]
		str = self.name + ": " + local_file + " <- " + remote_file  + "\n"
		if task:
			fd = task.output
		else:
			fd = sys.stdout
		fd.write(str)
		res = self._exec(cmd)
		fd.write(res)
		return res
	
	def get_result(self, command):
		return self._exec(["ssh", "root@%s" % self.name, command])

	def free_port(self, port, task):
		self.execute("for i in $(lsof -i:%s -t); do cat /proc/$i/status | fgrep PPid | cut -f2; done | xargs -r kill" % port, task)
		self.execute("lsof -i:%s -t | xargs -r kill" % port, task)

	def debug_info(self):		
		result={}
		result["top"] = self.get_result("top -n 1")
		result["OpenVZ"] = self.get_result("vzlist -a")
		result["KVM"] = self.get_result("qm list")
		result["Bridges"] = self.get_result("brctl show")
		result["iptables router"] = self.get_result("iptables -t mangle -v -L PREROUTING")		
		result["ipfw rules"] = self.get_result("ipfw show")
		result["ipfw pipes"] = self.get_result("ipfw pipe show")
		result["ifconfig"] = self.get_result("ifconfig -a")
		result["netstat"] = self.get_result("netstat -tulpen")		
		return result
	
class Template(models.Model):
		name = models.CharField(max_length=100)
		type = models.CharField(max_length=12)
		default = models.BooleanField(default=False)
		
		def __unicode__(self):
			return "Template(type=%s,name=%s,default=%s)" %(self.type, self.name, self.default)
			
def get_host(name):
	return Host.objects.get(name=name)

def get_host_group(name):
	return HostGroup.objects.get(name=name)
	
def get_host_groups():
	return HostGroup.objects.all()
	
def get_best_host(group):
	all = Host.objects.all()
	if group:
		all = all.filter(group__name=group)
	hosts = all.annotate(num_devices=models.Count('device')).order_by('num_devices', '?')
	if len(hosts) > 0:
		return hosts[0]
	else:
		raise fault.new(fault.NO_HOSTS_AVAILABLE, "No hosts available")

def get_templates(type=None):
	list = Template.objects.all()
	if type:
		list = list.filter(type=type)
	return list

def get_template(type, name):
	try:
		return Template.objects.get(type=type, name=name).name
	except Exception:
		return get_default_template(type)

def add_template(name, type):
	Template.objects.create(name=name, type=type)
	
def remove_template(name):
	Template.objects.filter(name=name).delete()
	
def get_default_template(type):
	list = Template.objects.filter(type=type, default=True)
	if list.count() >= 1:
		return list[0].name
	else:
		return None
	
def set_default_template(type, name):
	Template.objects.filter(type=type).update(default=False)
	Template.objects.filter(type=type, name=name).update(default=True)