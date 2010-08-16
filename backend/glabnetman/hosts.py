# -*- coding: utf-8 -*-

from django.db import models

import config

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
				
def get_host(name):
	return Host.objects.get(name=name)

def get_host_group(name):
	return HostGroup.objects.get(name=name)
	
def get_best_host(group):
	all = Host.objects.all()
	if group:
		all = all.filter(group__name=group)
	return all.annotate(num_devices=models.Count('device')).order_by('num_devices', '?')[1]

def next_free_port(host):
	ids = range(7000,8000)
	import openvz
	for dev in openvz.OpenVZDevice.objects.filter(host=host):
		ids.remove(dev.vnc_port)
	return ids[0]

def next_free_bridge(host):
	ids = range(1000,2000)
	import generic
	for con in generic.Connection.objects.filter(interface__device__host=host):
		ids.remove(con.bridge_id)
	return ids[0]