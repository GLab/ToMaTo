# -*- coding: utf-8 -*-

from django.db import models

import config, fault

class HostGroup(models.Model):
	name = models.CharField(max_length=10)
	
class Host(models.Model):
	group = models.ForeignKey(HostGroup)
	name = models.CharField(max_length=50)
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
		for dev in openvz.OpenVZDevice.objects.filter(host=self):
			ids.remove(dev.openvz_id)
		import kvm
		for dev in kvm.KVMDevice.objects.filter(host=self):
			ids.remove(dev.kvm_id)
		return ids[0]

	def next_free_port(self):
		ids = range(7000,8000)
		import openvz
		for dev in openvz.OpenVZDevice.objects.filter(host=self):
			ids.remove(dev.vnc_port)
		import kvm
		for dev in kvm.KVMDevice.objects.filter(host=self):
			ids.remove(dev.vnc_port)
		import tinc
		for con in tinc.TincConnection.objects.filter(interface__device__host=self):
			ids.remove(con.tinc_port)
		return ids[0]

	def next_free_bridge(self):
		ids = range(1000,2000)
		import generic
		for con in generic.Connection.objects.filter(interface__device__host=self):
			ids.remove(con.bridge_id)
		return ids[0]				
				
def get_host(name):
	return Host.objects.get(name=name)

def get_host_group(name):
	return HostGroup.objects.get(name=name)
	
def get_best_host(group):
	all = Host.objects.all()
	if group:
		all = all.filter(group__name=group)
	hosts = all.annotate(num_devices=models.Count('device')).order_by('num_devices', '?')
	if len(hosts) > 0:
		return hosts[0]
	else:
		raise fault.new(fault.NO_HOSTS_AVAILABLE, "No hosts available")